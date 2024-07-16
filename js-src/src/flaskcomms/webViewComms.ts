/**
 * This function is called when translating a web page.
 */
export const translateWeb = async (
  weblink: string,
  content_filter: string,
  do_preview: boolean
) => {
  const apiUrl = "http://localhost:5000/processweb";

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({
      weblink: weblink,
      content_filter: content_filter,
      do_preview: do_preview,
    }),
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");

  const data: any = await output.json();
  return data?.output as string;
};
