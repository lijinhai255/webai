const instance = axios.create({
  // baseURL: 'http://39.105.155.161:12406/',
  // baseURL: 'http://192.168.188.11:12406/',
  baseURL: "http://localhost:8000/",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
    Authorization: "Basic anp5ZXM6OGtJVWl1RkI=",
  },
});
function get(url, params) {
  return new Promise((resolve, reject) => {
    console.log(instance);

    instance
      .get(url, { params })
      .then((res) => {
        resolve(res.data);
      })
      .catch((err) => {
        reject(err.data);
      });
  });
}
function post(url, data) {
  return new Promise((resolve, reject) => {
    instance
      .post(url, data)
      .then((res) => {
        resolve(res.data);
      })
      .catch((err) => {
        reject(err);
      });
  });
}
