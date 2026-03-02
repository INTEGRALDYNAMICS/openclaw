import fs from "fs";

const configPath = process.env.HOME + "/.openclaw/openclaw.json";
const configStr = fs.readFileSync(configPath, "utf8");
const config = JSON.parse(configStr);

const token = config.gateway?.auth?.token || "1a7a1ea49d4cfc5687ab8c699937f1e591f28483f21bb9c1";
config.gateway = config.gateway || {};
config.gateway.auth = config.gateway.auth || {};
config.gateway.auth.token = token;
config.gateway.remote = config.gateway.remote || {};
config.gateway.remote.token = token;

fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log("Tokens synced to: " + token);
