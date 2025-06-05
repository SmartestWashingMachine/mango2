import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

export const setSeed = async (seed: number) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/setseed`;

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({ seed }),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 200) throw Error("Invalid status code.");
};

export const triggerCircuitBreak = async () => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/circuitbreak`;

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({}),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 200) throw Error("Invalid status code.");
};
