/**
 * Agent Work Queue Manager
 * Manages JSONL-based work queue for autonomous agent assignment
 */

const fs = require("fs");
const path = require("path");
const { appendJsonlQueued, readJsonl } = require("../apps/lantern-garage/lib/file-queue");

class QueueManager {
  constructor(queuePath) {
    this.queuePath = queuePath || path.join(process.cwd(), "data", "agent-work-queue");
    this.ensureStructure();
  }

  ensureStructure() {
    const dirs = ["pending", "assigned", "completed", "failed"];
    for (const dir of dirs) {
      const dirPath = path.join(this.queuePath, dir);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
      }
    }
  }

  /**
   * Add work item to pending queue
   */
  async enqueueWork(issueData) {
    const entry = {
      id: `issue-${issueData.issueNumber}`,
      issueNumber: issueData.issueNumber,
      title: issueData.title,
      description: issueData.description || "",
      priority: issueData.priority || 0,
      assignedTo: null,
      assignedAt: null,
      status: "pending",
      branch: null,
      targetDate: issueData.targetDate || null,
      retries: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const pendingFile = path.join(this.queuePath, "pending", `${entry.id}.json`);
    fs.writeFileSync(pendingFile, JSON.stringify(entry, null, 2));
    return entry;
  }

  /**
   * Get next available work item for an agent
   */
  async getNextWork(agentId) {
    const pendingDir = path.join(this.queuePath, "pending");
    const files = fs.readdirSync(pendingDir).filter((f) => f.endsWith(".json"));

    if (files.length === 0) return null;

    // Sort by priority (descending) and creation time (ascending)
    const items = files
      .map((f) => {
        const data = JSON.parse(fs.readFileSync(path.join(pendingDir, f), "utf8"));
        return data;
      })
      .sort((a, b) => {
        if (b.priority !== a.priority) return b.priority - a.priority;
        return new Date(a.createdAt) - new Date(b.createdAt);
      });

    const nextItem = items[0];

    // Assign to agent
    nextItem.assignedTo = agentId;
    nextItem.assignedAt = new Date().toISOString();
    nextItem.status = "assigned";
    nextItem.branch = `${agentId}/issue-${nextItem.issueNumber}`;
    nextItem.updatedAt = new Date().toISOString();

    // Move to assigned
    const assignedFile = path.join(this.queuePath, "assigned", `${nextItem.id}.json`);
    fs.writeFileSync(assignedFile, JSON.stringify(nextItem, null, 2));

    // Remove from pending
    fs.unlinkSync(path.join(pendingDir, `${nextItem.id}.json`));

    return nextItem;
  }

  /**
   * Mark work item as completed
   */
  async markComplete(workId, result) {
    const assignedFile = path.join(this.queuePath, "assigned", `${workId}.json`);
    if (!fs.existsSync(assignedFile)) {
      throw new Error(`Work item ${workId} not found in assigned queue`);
    }

    const entry = JSON.parse(fs.readFileSync(assignedFile, "utf8"));
    entry.status = "completed";
    entry.completedAt = new Date().toISOString();
    entry.result = result;
    entry.updatedAt = new Date().toISOString();

    // Move to completed
    const completedFile = path.join(this.queuePath, "completed", `${workId}.json`);
    fs.writeFileSync(completedFile, JSON.stringify(entry, null, 2));

    // Remove from assigned
    fs.unlinkSync(assignedFile);

    return entry;
  }

  /**
   * Mark work item as failed
   */
  async markFailed(workId, error) {
    const assignedFile = path.join(this.queuePath, "assigned", `${workId}.json`);
    if (!fs.existsSync(assignedFile)) {
      throw new Error(`Work item ${workId} not found in assigned queue`);
    }

    const entry = JSON.parse(fs.readFileSync(assignedFile, "utf8"));
    entry.retries = (entry.retries || 0) + 1;
    entry.lastError = error;
    entry.updatedAt = new Date().toISOString();

    if (entry.retries >= 3) {
      entry.status = "failed";
      const failedFile = path.join(this.queuePath, "failed", `${workId}.json`);
      fs.writeFileSync(failedFile, JSON.stringify(entry, null, 2));
      fs.unlinkSync(assignedFile);
    } else {
      entry.status = "pending";
      const pendingFile = path.join(this.queuePath, "pending", `${workId}.json`);
      fs.writeFileSync(pendingFile, JSON.stringify(entry, null, 2));
      fs.unlinkSync(assignedFile);
    }

    return entry;
  }

  /**
   * Get queue status
   */
  async getStatus() {
    const pending = fs.readdirSync(path.join(this.queuePath, "pending")).filter((f) => f.endsWith(".json")).length;
    const assigned = fs.readdirSync(path.join(this.queuePath, "assigned")).filter((f) => f.endsWith(".json")).length;
    const completed = fs.readdirSync(path.join(this.queuePath, "completed")).filter((f) => f.endsWith(".json")).length;
    const failed = fs.readdirSync(path.join(this.queuePath, "failed")).filter((f) => f.endsWith(".json")).length;

    return {
      pending,
      assigned,
      completed,
      failed,
      total: pending + assigned + completed + failed,
    };
  }

  /**
   * List all work items by status
   */
  async listByStatus(status) {
    const dir = path.join(this.queuePath, status);
    if (!fs.existsSync(dir)) return [];

    const files = fs.readdirSync(dir).filter((f) => f.endsWith(".json"));
    return files.map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")));
  }
}

module.exports = QueueManager;
