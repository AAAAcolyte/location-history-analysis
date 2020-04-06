import Vue from 'vue'
import Router from 'vue-router'
import fileUpload from '../components/fileUpload.vue'
import introduction from '../components/introduction.vue'

Vue.use(Router)
const routes = [
    {path:'/upload', component: fileUpload},
    {path:'/intro', component:introduction},
    {path:'*', redirect: '/intro'}
]
export default new Router({
    routes
})