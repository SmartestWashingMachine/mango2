import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

export const getInstalledModels = async () => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/allowedmodels`;

  try {
    const output = await fetch(apiUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });

    if (output.status !== 200) throw Error("Invalid status code.");

    return output.json();
  } catch (err) {
    console.log(err);
  }
};
