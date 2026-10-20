# Attendance Sync — Android APK project

## Included
- Editable and locally saved IP, port, and branch code
- Test Connection button
- Start Attendance Sync button
- First run: all records; later runs: last 30 days
- Sends batches of 5,000 to the existing Google Apps Script endpoint
- Saves sync marker only when all batches succeed
- GitHub Actions workflow to attempt a cloud APK build

Defaults:
- IP: `10.16.15.12`
- Port: `4370`
- Branch: `BNS`

## Important network requirement
The phone must be able to reach the ZKTeco device over the network. If the phone is outside the company LAN, a properly configured VPN or other secure network route is required. Mobile data alone will not normally reach a private `10.x.x.x` IP.

## Build APK on Linux / WSL2
Install Java 17, Android SDK command-line tools and Buildozer prerequisites, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install buildozer cython==0.29.36
buildozer android debug
```

The APK is normally created under `bin/`.

## Cloud build via GitHub Actions
1. Create a GitHub repository and upload the contents of this project to the repository's `main` branch.
2. Open the repository's **Actions** tab and run **Build Attendance Sync APK** (or push a commit to `main`).
3. If the build succeeds, open the completed workflow run and download the `AttendanceSync-debug-apk` artifact. Extract it to get the `.apk` file.

The cloud workflow is a build attempt, not a guarantee: the first build may fail if Android packaging of `pyzk` needs compatibility changes.

## Compatibility and operational notes
- This is source code, not a prebuilt APK.
- The `pyzk` package may require Android-specific compatibility adjustments; confirm the build and test on the actual phone and device.
- The Google Apps Script endpoint is embedded in `main.py` and must remain deployed and accessible.
- The app rescans the last 30 days on subsequent runs. Duplicate avoidance depends on the server-side Apps Script implementation.
