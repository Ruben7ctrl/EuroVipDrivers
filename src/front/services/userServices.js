const userServices = {};

const backendUrl = import.meta.env.VITE_BACKEND_URL;

userServices.register = async (formData) => {
  try {
    const base = backendUrl?.endsWith("/") ? backendUrl : backendUrl + "/";
    const url = base + "api/signup";
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });
    const contentType = resp.headers.get("content-type") || "";
    if (!resp.ok) {
      let details = "";
      if (contentType.includes("application/json")) {
        const err = await resp.json().catch(() => ({}));
        details = err?.error || JSON.stringify(err);
      } else {
        const text = await resp.text().catch(() => "");
        details = text?.slice(0, 200);
      }
      throw new Error(`Request failed ${resp.status}: ${details}`);
    }
    const data = contentType.includes("application/json")
      ? await resp.json()
      : await resp.text();
    return data;
  } catch (error) {
    console.log(error);
    throw error;
  }
};

export default userServices;
