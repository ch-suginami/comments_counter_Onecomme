const LIMIT = 30
const app = Vue.createApp({
  setup() {
    document.body.removeAttribute('hidden')
  },
  data() {
    return {
      comments: []
    }
  },
  methods: {
    getClassName(comment) {
      if (comment.commentIndex % 2 === 0) {
        return 'comment even'
      }
      return 'comment odd'
    },
    getStyle(comment) {
      return OneSDK.getCommentStyle(comment)
    }
  },
  mounted() {
    const WAIT_DURATION = OneSDK.getStyleVariable('--lcv-wait-duration', 100, parseInt)
    const INTERVAL = OneSDK.getStyleVariable('--lcv-enter-duration', 160, parseInt) + WAIT_DURATION
    const LIFE_TIME = OneSDK.getStyleVariable('--lcv-lifetime', 5000, parseInt) + WAIT_DURATION

    commentIndex = 0
    OneSDK.setup({
      mode: 'diff',
      disabledDelay: true,
      protocol: "ws",
      host: "127.0.0.2",
      port: 11181,
      commentLimit: LIMIT,
      permissions: OneSDK.usePermission([OneSDK.PERM.COMMENT])
    })
    const queue = []
    OneSDK.subscribe({
      action: 'comments',
      callback: (comments) => {
        if (comments.length !== 0) {
          queue.push(...comments)
        }
      }
    })

    let time = 0
    const check = () => {
      const now = Date.now()
      if (time + INTERVAL < now) {
        if (queue.length !== 0) {
          time = now
          const comment = queue.shift()
          this.comments.shift()
          this.comments.push(comment)
        } else if (now - time > LIFE_TIME) {
          this.comments.shift()
        }
      }
      requestAnimationFrame(check)
    }
    OneSDK.connect()
    check()
  },
})
OneSDK.ready().then(() => {
  app.mount("#container");
})

