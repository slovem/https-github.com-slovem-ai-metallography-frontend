import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import Login from '@/views/auth/Login.vue'
import Register from '@/views/auth/Register.vue'

// 导入所有页面
import Dashboard from '@/views/dashboard/Dashboard.vue'
import TaskList from '@/views/task/TaskList.vue'
import TaskCreate from '@/views/task/TaskCreate.vue'
import TaskDetail from '@/views/task/TaskDetail.vue'
import Learning from '@/views/learning/Learning.vue'
import Annotation from '@/views/annotation/Annotation.vue'
import SearchView from '@/views/search/SearchView.vue'
import Profile from '@/views/profile/Profile.vue'
import RolePermission from '@/views/system/RolePermission.vue'
import UserAudit from '@/views/system/UserAudit.vue'  // ✅ 导入用户审核页面

const routes = [
  {
    path: '/auth/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', public: true }
  },
  {
    path: '/auth/register',
    name: 'Register',
    component: Register,
    meta: { title: '注册', public: true }
  },
  {
    path: '/',
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard, meta: { title: '数据看板' } },
      { path: 'tasks', component: TaskList, meta: { title: '检测任务' } },
      { path: 'tasks/create', component: TaskCreate, meta: { title: '新建任务' } },
      { path: 'tasks/:id', component: TaskDetail, meta: { title: '任务详情' } },
      { path: 'learning', component: Learning, meta: { title: '模型学习' } },
      { path: 'annotation', component: Annotation, meta: { title: '数据标注' } },
      { path: 'search', component: SearchView, meta: { title: '以图搜图' } },
      { path: 'profile', component: Profile, meta: { title: '个人中心' } },
      { path: 'system', redirect: '/system/roles' },
      { path: 'system/roles', component: RolePermission, meta: { title: '角色权限管理' } },
      { path: 'system/users', component: UserAudit, meta: { title: '用户审核' } }  // ✅ 添加这一行
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

let isFetching = false

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const token = localStorage.getItem('token')

  if (to.meta?.public) {
    if (token && to.path === '/auth/login') {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  if (!token) {
    next('/auth/login')
    return
  }

  if (!isFetching) {
    isFetching = true
    await authStore.fetchPermissions()
    isFetching = false
  }

  next()
})

export default router