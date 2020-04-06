import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import router from './router/router.js'
import VueSessionStorage from 'vue-sessionstorage';
import VueLocalStorage from 'vue-localstorage'
import 'material-design-icons-iconfont/dist/material-design-icons.css';

Vue.config.productionTip = false

Vue.use(VueSessionStorage)
Vue.use(VueLocalStorage)

new Vue({
  vuetify,
  router,
  render: h => h(App)
}).$mount('#app')
