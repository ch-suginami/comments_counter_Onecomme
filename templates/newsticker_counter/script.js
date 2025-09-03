const LIMIT = 30
let temp = []
let queues = []
const app = Vue.createApp({
  setup() {
    document.body.removeAttribute('hidden')
  },
  data() {
    return {
      intervalTime: 0,
      waiting: false,
      interval: 5000,
      lifeTime: 5000,
      delay: 300,
      comments: [],
    }
  },
  methods: {
    onEnd() {
      this.comments = []
      setTimeout(() => {
        this.waiting = false
        this.next()
      })
    },
    next() {
      if (this.waiting) return
      const q = queues.shift()
      if (q) {
        this.waiting = true
        this.comments.push(q)
      }
    },
    updateInterval() {
      const now = performance.now()
      this.interval = Math.min(now - this.intervalTime, 5000)
      this.intervalTime = now
      this.lifeTime = this.interval / queues.length
    },
  },
  mounted() {
    const TIMER_INTERVAL = OneSDK.getStyleVariable('--lcv-interval', 4000, parseInt)
    this.delay = OneSDK.getStyleVariable('--lcv-delay', 300, parseInt)

    OneSDK.setup({
      mode: 'diff',
      disabledDelay: true,
      permissions: OneSDK.usePermission([OneSDK.PERM.COMMENT]),
      protocol: "ws",
      host: "127.0.0.2",
      port: 11181,
      commentLimit: LIMIT
    })
    const check = () => {
      if (temp.length !== 0) {
        queues.push(...temp)
        temp = []
      }
      this.updateInterval()
      this.next()
    }
    let initialized = false
    this.intervalTime = performance.now()
    OneSDK.subscribe({
      action: 'comments',
      callback: comments => {
        if (comments.length !== 0) {
          temp.push(...comments)
          if (!initialized) {
            initialized = true
            check()
            setInterval(check, TIMER_INTERVAL)
          }
        }
      },
    })
    OneSDK.connect()
  },
})
app.component('comment', {
  props: ['id', 'comment', 'life-time', 'delay', 'onEnd'],
  methods: {
    getStyle(comment) {
      return OneSDK.getCommentStyle(comment)
    },
    getLifeTime() {
      return this.lifeTime
    },
    ease(t, b, c, d) {
      return (c * t) / d + b
    },
  },
  mounted() {
    const { container } = this.$refs
    const b = performance.now()
    const _lifeTime = this.lifeTime
    const _maxTime = Math.min(_lifeTime, 2000)
    const width = container.offsetWidth
    const inner = container.querySelector('.comment-inner')
    this.x = Math.max(container.scrollWidth - width, 0)
    const tick = t => {
      if (t - b >= _lifeTime - this.delay) {
        const x = this.ease(Math.min(t - b, _maxTime), 0, -this.x, _maxTime)
        inner.style.transform = `translateX(${x}px)`
        if (t - b >= _lifeTime) {
          this.$emit('end', this.id)
          return
        }
      } else if (t - b >= this.delay && t - b < _maxTime) {
        const x = this.ease(t - b, 0, -this.x, _maxTime)
        inner.style.transform = `translateX(${x}px)`
      }
      requestAnimationFrame(tick)
    }
    tick(b)
  },
  template: `
    <div class="comment-container" :key="id" ref="container" :style="getStyle(comment)">
      <div class="comment-inner">
        <span class="body">
          <span v-if="comment.data.paidText" class="paid-text">
            {{comment.data.paidText}}
          </span>
          <span v-if="comment.data.membership" class="paid-text">
            {{comment.data.membership.sub}} {{comment.data.membership.primary}}
          </span>
          <span class="text" v-html="comment.data.comment"></span>
        </span>
      </div>
    </div>
  `,
})
OneSDK.ready().then(() => {
  app.mount('#container')
})
