import * as axios from 'axios';

const BASE_URL = 'http://localhost:5000';

function upload(file) {
    const url = `${BASE_URL}/upload`;
    var formData = new FormData();
    formData.append("file", file);
    return axios.post(url, formData)
}

export { upload }