const assert = require("assert");
const { parseBangCommand } = require("../apps/lantern-garage/lib/dream-chat");

function run() {
  const cases = [
    ["", null],
    ["   ", null],
    ["!", null],
    ["not a command", null],
    [" !debug  ", { name: "debug", args: "" }],
    ["!REPORT today", { name: "report", args: "today" }],
    ["!three-doors forest path", { name: "three-doors", args: "forest path" }],
    ["!export    latest", { name: "export", args: "latest" }],
    ["!weird/chars arg text", { name: "weird/chars", args: "arg text" }],
  ];

  for (const [input, expected] of cases) {
    assert.deepStrictEqual(parseBangCommand(input), expected, `parseBangCommand(${JSON.stringify(input)})`);
  }

  console.log(`${cases.length}/${cases.length} parser cases passed`);
}

run();
