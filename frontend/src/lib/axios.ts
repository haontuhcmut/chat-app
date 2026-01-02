import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.MODE === 'development' ? "http://localhost/api/v1" : "/api/v1",
    withCredentials: true
})

export default api