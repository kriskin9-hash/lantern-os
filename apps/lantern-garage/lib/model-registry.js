/**
 * Canonical Model Registry for Lantern OS
 * Maps model profiles to Ollama models and surface usage
 */

// Model registry with configurations for all surfaces
module.exports = {
  text: {
    keystone: {
      profileId: "keystone-ft",
      ftAgentId: "agent_01XLCumJKAJzNtUiB1FQTWrT",
      memoryStoreId: "memstore_01WYD6jnTDjbCDGPSHGWPeqx",
      baseModel: "claude-haiku-4-5-20251001",
      trainingData: "data/training/haiku-ft-pairs.jsonl",
      surfaces: ["dream-chat", "orchestration", "code-execution"],
    },
    dream: {
      profileId: "lantern-csf-dream",
      ollamaModel: process.env.DREAMCHAT_MODEL || "lantern-csf-dream",
      surfaces: ["dream-chat", "dream-journal", "three-doors"],
    },
    pcsf: {
      profileId: "lantern-pcsf",
      ollamaModel: process.env.PCSF_MODEL || "lantern-pcsf",
      surfaces: ["provider-routing", "privacy", "receipts"],
    },
    convergance: {
      profileId: "lantern-convergance",
      ollamaModel: process.env.CONVERGENCE_MODEL || "lantern-convergance",
      surfaces: ["eval", "promotion", "receipts", "task-loop"],
    },
  },
  image: {
    dream: {
      modelId: "lantern-csf-dream-image",
      adapterPath:
        process.env.LANTERN_IMAGE_LORA ||
        "models/csf-image/checkpoints/lantern-door-lora-final.safetensors",
      surfaces: ["dream-journal", "three-doors"],
      status: "hold-pending-validation",
    },
  },
};
