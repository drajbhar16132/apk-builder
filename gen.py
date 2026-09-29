import json, os, shutil
from xml.sax.saxutils import escape

c = json.load(open('config.json', encoding='utf-8'))
pkg, name = c['package'], c['name']
target = c['url'] if c['mode'] == 'url' else 'file:///android_asset/index.html'
ads = c.get('ads', {})
use_ads = bool(ads.get('on'))
app_id = ads.get('appId') or 'ca-app-pub-3940256099942544~3347511713'
unit_id = ads.get('unitId') or 'ca-app-pub-3940256099942544/6300978111'
deps = '\ndependencies {\n    implementation "com.google.android.gms:play-services-ads:23.6.0"\n}\n' if use_ads else ''
ads_imports = 'import android.view.Gravity;\nimport com.google.android.gms.ads.AdRequest;\nimport com.google.android.gms.ads.AdSize;\nimport com.google.android.gms.ads.AdView;\nimport com.google.android.gms.ads.MobileAds;\n' if use_ads else ''
ads_code = ('        MobileAds.initialize(this);\n        AdView ad = new AdView(this);\n        ad.setAdSize(AdSize.BANNER);\n        ad.setAdUnitId(' + json.dumps(unit_id) + ');\n        LinearLayout.LayoutParams alp = new LinearLayout.LayoutParams(-2, -2);\n        alp.gravity = Gravity.CENTER_HORIZONTAL;\n        root.addView(ad, alp);\n        ad.loadAd(new AdRequest.Builder().build());\n') if use_ads else ''
meta = ('        <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="' + app_id + '" />\n') if use_ads else ''

def w(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)

w('settings.gradle', """pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "WebApp"
include ":app"
""")
w('build.gradle', 'plugins {\n    id "com.android.application" version "8.2.2" apply false\n}\n')
w('gradle.properties', 'org.gradle.jvmargs=-Xmx2g\nandroid.useAndroidX=true\n')
w('app/build.gradle', """plugins { id "com.android.application" }
android {
    namespace "PKG"
    compileSdk 34
    defaultConfig {
        applicationId "PKG"
        minSdk 21
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}
""".replace('PKG', pkg) + deps)
w('app/src/main/AndroidManifest.xml', """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:label="@string/app_name"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""".replace('    </application>', meta + '    </application>'))
w('app/src/main/res/values/strings.xml',
  '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">'
  + escape(name).replace("'", "\\'") + '</string>\n</resources>\n')
w('app/src/main/java/' + pkg.replace('.', '/') + '/MainActivity.java', """package PKG;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
ADS_IMPORTS
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        web = new WebView(this);
        root.addView(web, new LinearLayout.LayoutParams(-1, 0, 1f));
ADS_CODE        setContentView(root);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        web.setWebViewClient(new WebViewClient());
        if (b == null) web.loadUrl(TARGET);
        else web.restoreState(b);
    }

    @Override
    protected void onSaveInstanceState(Bundle b) {
        super.onSaveInstanceState(b);
        web.saveState(b);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
""".replace('PKG', pkg).replace('TARGET', json.dumps(target)).replace('ADS_IMPORTS', ads_imports).replace('ADS_CODE', ads_code))

if c['mode'] == 'html':
    os.makedirs('app/src/main/assets', exist_ok=True)
    shutil.copy('index.html', 'app/src/main/assets/index.html')
if os.path.exists('icon.png'):
    os.makedirs('app/src/main/res/mipmap-xxxhdpi', exist_ok=True)
    shutil.copy('icon.png', 'app/src/main/res/mipmap-xxxhdpi/ic_launcher.png')
