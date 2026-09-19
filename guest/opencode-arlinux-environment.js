export default async () => ({
  "shell.env": async (_input, output) => {
    output.env.NO_AT_BRIDGE = "0"
  },
})
