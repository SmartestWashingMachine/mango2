const cp = require("child_process");

// Partially vibe coded.
export const hasGpu = () => {
  try {
    console.log("Checking if user has a capable GPU...");

    const cvd = process.env.CUDA_VISIBLE_DEVICES;

    console.log(`CUDA_VISIBLE_DEVICES : ${cvd}`);

    // Check for explicit "hide" command
    if (cvd === "" || cvd === "-1" || cvd === '""') {
      console.log("User has no CUDA visible devices - returning false!");
      return false;
    }

    // Query the driver version directly
    const output = cp
      .execSync("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
      .toString()
      .trim();

    console.log(`GPU Check Output: ${output}`);

    // Handle multi-GPU systems (get the first one)
    // ... though this shouldn't be necessary. As far as I know all of you are running this app on single GPU workloads.
    const driverVersionStr = output.split("\n")[0];
    const driverVersion = parseFloat(driverVersionStr);

    console.log(`GPU Check Version: ${driverVersion}`);

    // (according to AI):
    // SPECIFIC LOGIC FOR CUDA 12.4 ON WINDOWS:
    // 1. If below 527.41, it's a hard "NO".
    // 2. If between 527.41 and 551.77, it's "YES" (via Minor Version Compatibility).
    // 3. If 551.78 or higher, it's "FULL SUPPORT".

    if (isNaN(driverVersion)) throw new Error("Could not parse driver version");

    return driverVersion >= 527.41;
  } catch (err) {
    console.error(err);
    return false;
  }
};
