# 달의 안부 — Android / Google Play 출시 준비

## 현재 범위

웹주소로 접속하지 않고 앱 안의 HTML/JS 및 카드 이미지 78장을 사용하는 Capacitor Android 프로젝트입니다. 현재 여섯 스프레드, 셔플, 중복 없는 추첨, 카드 도감, 로컬 리딩 기록, 사용자 지정 이미지 선택을 포함합니다. 기본 리딩에는 서버나 로그인이 필요 없습니다.

- 앱 이름: 달의 안부
- 애플리케이션 ID: `com.gchunhwa2maker.moonlittarot`
- 버전: 1.0.0 / versionCode 1
- Android 7.0(API 24) 이상, compile/target SDK 36
- 개발 도구: Node.js 22 이상, npm, Python 3, JDK 21, Android SDK 36
- 의존성 버전은 package-lock.json에 고정합니다.
- 공개 전 앱 ID와 개발자 표시 이름을 확정하세요. 출시 후 앱 ID를 바꾸면 별개의 앱이 됩니다.

## 빌드

Android Studio에서 SDK Platform 36과 Build Tools 36.0.0을 설치하세요. `ANDROID_HOME`으로 SDK 위치를 지정하거나, 추적되지 않는 `android/local.properties`에 SDK 경로를 설정합니다.

```sh
npm ci
npm run android:sync
npm run android:debug
```

설치 테스트용 파일: `android/app/build/outputs/apk/debug/app-debug.apk`. Android 휴대폰에서 설치·확인하는 용도입니다. Play 제출 파일이 아니며 iPhone에는 설치할 수 없습니다.

## 정식 업로드 서명

Android Studio의 **Build → Generate Signed App Bundle / APK → Android App Bundle**에서 본인 소유의 업로드 키를 만들고 안전하게 보관하세요. Play App Signing을 이용하며 키와 암호는 Git이나 채팅에 올리지 않습니다.

이 프로젝트의 CLI 서명은 아래 네 환경변수를 읽습니다. 값은 비밀 관리 도구나 로컬 셸에 안전하게 설정하세요.

- `MOONLIT_UPLOAD_STORE_FILE`: 본인 소유 업로드 keystore의 절대 경로
- `MOONLIT_UPLOAD_STORE_PASSWORD`
- `MOONLIT_UPLOAD_KEY_ALIAS`
- `MOONLIT_UPLOAD_KEY_PASSWORD`

```sh
npm run android:bundle
```

서명된 제출 파일: `android/app/build/outputs/bundle/release/app-release.aab`.

서명이 없으면 일반 릴리스 빌드는 실패하도록 구성했습니다. 기술 검증에만 사용할 때는 `./gradlew bundleRelease -PallowUnsignedReleaseValidation`로 서명 없는 번들을 생성할 수 있습니다. 이 파일은 스토어에 제출할 수 없습니다. 파일 확장자가 AAB라는 사실만으로 제출 준비가 끝난 것은 아닙니다.

서명 후 `jarsigner -verify -verbose -certs <파일>` 및 Play Console의 번들 검증으로 확인하세요. 정식 출시에는 debug 키를 사용하지 않습니다.

## 출시 전에 사용자에게 필요한 것

1. Google Play Console 개발자 계정, 본인/조직 및 기기 인증. 계정 유형에 따라 콘솔이 요구하는 비공개 테스트를 완료합니다.
2. 앱 운영자 표시 이름, 문의 이메일, 공개 HTTPS 개인정보처리방침 URL. 현재 privacy.html은 운영자/문의 정보를 확정하지 않은 초안이며 아직 공개 게시하지 않았습니다.
3. 업로드 키와 Play App Signing 설정. 키의 생성·보관은 사용자 소유로 진행합니다.
4. 실기기 테스트, 최종 스크린샷과 스토어 이미지, 콘텐츠 등급/대상 연령/데이터 보안/광고 여부 설문.
5. 실제 포함한 카드 이미지의 출처·권리 검토 완료. 현재 원본 RWS 그림은 기존 GitHub 출처이며 Wikimedia 개별 파일 확인 작업은 미완료입니다. 관련 기록: assets/cards/SOURCES.md. 위키미디어에서 검증됐다고 기재하지 마세요.

이 항목이 해결되지 않으면 ‘등록 완료’ 또는 ‘심사 통과’라고 표시하지 않습니다. Play 정책과 SDK 요구 사항은 제출 당시 콘솔의 안내를 다시 확인하세요.

## 실제 데이터 처리에 따른 설문 초안

현재 앱에는 광고, 계정, 결제, 분석 SDK, 자체 서버 업로드가 없습니다. 최근 리딩은 앱의 localStorage에만 저장합니다. 기록 삭제 기능을 제공하고 Android 백업은 비활성화했습니다. 사용자 지정 이미지는 시스템 파일 선택기로 선택해 세션 동안 표시하며 전송하지 않습니다. 카메라/연락처/위치 권한은 요청하지 않습니다. 외부 출처 링크를 열 때는 외부 사이트의 처리가 적용됩니다.

이 설명은 현 구현 기준의 초안입니다. 운영자가 출시 버전 및 SDK를 확인한 뒤 설문에 답해야 하며, 추후 광고/분석/결제가 추가되면 수정해야 합니다.

## 출시 확인

- 실기기에서 최초 실행을 비행기 모드로 테스트: 6개 스프레드, 78장 도감, 이미지
- 리딩 기록을 저장하고 종료/재실행해 유지 여부 및 삭제 확인
- 시스템 파일 선택, 사용자 지정 이미지, 회전, 뒤로 가기, 노치/시스템바 배치
- TalkBack/글꼴 확대, 앱 아이콘/스플래시, 지원 최소 버전과 최신 Android
- 서명된 AAB를 내부 테스트 트랙에 업로드하고 Pre-launch report 점검
- 서명 없는 번들/브라우저 테스트는 실기기 검증을 대신하지 않습니다.

## 공개와 저장소

기존 GitHub Pages 웹사이트는 별도로 유지됩니다. Android 소스 작업을 했다고 자동으로 스토어에 공개되거나 기존 웹사이트가 업데이트되지는 않습니다. 앱 업데이트에는 versionCode를 올려 새 AAB를 제출해야 합니다.
