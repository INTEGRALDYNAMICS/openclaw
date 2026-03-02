import fs from "fs";

const configPath = process.env.HOME + "/.openclaw/openclaw.json";
const configStr = fs.readFileSync(configPath, "utf8");
const config = JSON.parse(configStr);

config.models.providers.nvidia.baseUrl = "https://integrate.api.nvidia.com/v1";
config.models.providers.nvidia.models = [
  { id: "minimaxai/minimax-m2.1", name: "Minimax 2.1" },
  { id: "qwen/qwen3.5-397b-a17b", name: "Qwen 3.5 397B" },
];

fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log("Config fixed");
