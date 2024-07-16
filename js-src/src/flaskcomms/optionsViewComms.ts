export const setSeed = async (seed: number) => {
  const apiUrl = "http://localhost:5000/setseed";

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
