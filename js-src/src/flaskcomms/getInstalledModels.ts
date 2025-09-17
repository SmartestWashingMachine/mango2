import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const getInstalledModels = async () => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/allowedmodels`;

  // while(True) is blasphemy. But in Mango we 99% know the request will EVENTUALLY go through.
  while (true) {
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

    console.log("Retrying /allowedmodels GET call in 3 seconds...");
    await delay(3000);
  }
};
