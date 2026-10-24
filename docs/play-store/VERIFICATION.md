# Android build verification — 2026-10-24

Built debug APK and unsigned AAB successfully with JDK 21, SDK/target 36 and Gradle 8.14.3.

Application lint: 0 fatal, 0 errors, 11 warnings. Remaining warnings are template/unused-resource items. Dependency lint uses the existing upstream Capacitor baseline; it was not disabled or edited.

Passed: 6 Node tests; 4 importer validation tests using fixtures (not live Wikimedia checks); Chromium functional validation of bundled Android web assets for all six spreads, 78 images and persistence/deletion without remote requests. Debug APK signature verified with apksigner. Both packages contain 78 JPEG cards. Unsigned release builds are blocked unless the explicit validation flag is supplied.

Not run: Android device/emulator installation, Android Studio signing wizard, user-owned release signing, Play Console upload, Play pre-launch report, Play review. The unsigned AAB is not a store submission artifact.

Local output: dist/android-builds/. The GitHub workflow can produce equivalent validation artifacts; cloud workflow success has not been independently confirmed here.

## moonlit-debug.apk
- Bytes: 12196454
- SHA-256: 0c5807d22089e40cc455c33301de7f974360f49dbd49cd680ecbf455288b16d1

## moonlit-release-UNSIGNED.aab
- Bytes: 10777348
- SHA-256: b29b41534380dec2fa7954bd81efb21c5bb1ad0183be4051d65211fecb5c5094
