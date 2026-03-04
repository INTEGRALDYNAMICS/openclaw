import fs from "fs";

const configPath = process.env.HOME + "/.openclaw/openclaw.json";
const configStr = fs.readFileSync(configPath, "utf8");
const config = JSON.parse(configStr);

// add nvidia api key
config.models = config.models || {};
config.models.providers = config.models.providers || {};
config.models.providers.nvidia = config.models.providers.nvidia || {};
config.models.providers.nvidia.apiKey = "nvapi-REDACTED";

// set default model
config.agents = config.agents || {};
config.agents.defaults = config.agents.defaults || {};
config.agents.defaults.model = config.agents.defaults.model || {};
config.agents.defaults.model.primary = "nvidia/minimaxai/minimax-m2.1";

// make sure both are populated
config.agents.defaults.models = config.agents.defaults.models || {};
config.agents.defaults.models["nvidia/minimaxai/minimax-m2.1"] = {};
config.agents.defaults.models["nvidia/qwen/qwen3.5-397b-a17b"] = {};

fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log("Config updated");
