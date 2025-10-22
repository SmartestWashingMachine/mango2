export const scanScreenGiveData = async () => {
  // This always goes to local host first - the backend there will then push it to the remote backend.
  const apiUrl = `http://127.0.0.1:5000/scanscreen`;

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
