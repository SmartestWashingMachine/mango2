/**
 * This function is called when previewing the captured window from the global options view.
 */
export const previewCaptureWindow = async (coords?: number[]) => {
  const apiUrl = "http://localhost:5000/previewwindowcapture";

  const formData = new FormData();
  if (coords) {
    formData.append("x1", coords[0].toString());
    formData.append("y1", coords[1].toString());
    formData.append("width", coords[2].toString());
    formData.append("height", coords[3].toString());
  }

  const output = await fetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");

  const data = await output.json();

  return data["image_base64"] || "";
};
