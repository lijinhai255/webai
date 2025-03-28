const instance = axios.create({
  // baseURL: 'http://39.105.155.161:12406/',
  baseURL: "http://127.0.0.1:8000/",
  // baseURL: "http://23.95.36.253:80/",
  timeout: 60000,
  changeOrigin: true, // 改变请求的来源
  pathRewrite: { "^/api": "" }, // 重写路径，去掉 `/api` 前缀
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
