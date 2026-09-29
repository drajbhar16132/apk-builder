import json, os, re, shutil
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

sp = c.get('splash', {})
use_splash = bool(sp.get('on'))
sp_style = sp.get('style') if sp.get('style') in ('zoom', 'bounce', 'spin', 'pulse') else 'zoom'
sp_bg = sp.get('bg') if re.fullmatch(r'#[0-9a-fA-F]{6}', str(sp.get('bg', ''))) else '#1f7a4d'
try:
    sp_ms = min(max(int(sp.get('ms', 3000)), 1000), 6000)
except (TypeError, ValueError):
    sp_ms = 3000
sp_lum = 0.299 * int(sp_bg[1:3], 16) + 0.587 * int(sp_bg[3:5], 16) + 0.114 * int(sp_bg[5:7], 16)
sp_fg = '#000000' if sp_lum > 160 else '#FFFFFF'

sp_anims = {
    'zoom': """            spLogo.setScaleX(0.3f);
            spLogo.setScaleY(0.3f);
            spLogo.setAlpha(0f);
            spLogo.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(800).setInterpolator(new OvershootInterpolator()).start();
""",
    'bounce': """            spLogo.setTranslationY(-300 * spD);
            spLogo.setAlpha(0f);
            spLogo.animate().translationY(0f).alpha(1f).setDuration(1000).setInterpolator(new BounceInterpolator()).start();
""",
    'spin': """            spLogo.setScaleX(0f);
            spLogo.setScaleY(0f);
            spLogo.setRotation(-360f);
            spLogo.animate().scaleX(1f).scaleY(1f).rotation(0f).setDuration(1000).setInterpolator(new DecelerateInterpolator()).start();
""",
    'pulse': """            spLogo.setAlpha(0f);
            spLogo.animate().alpha(1f).setDuration(600).start();
            ObjectAnimator spPulse = ObjectAnimator.ofPropertyValuesHolder(spLogo,
                PropertyValuesHolder.ofFloat("scaleX", 1f, 1.15f),
                PropertyValuesHolder.ofFloat("scaleY", 1f, 1.15f));
            spPulse.setDuration(700);
            spPulse.setStartDelay(600);
            spPulse.setRepeatCount(ValueAnimator.INFINITE);
            spPulse.setRepeatMode(ValueAnimator.REVERSE);
            spPulse.start();
            spKeep[0] = spPulse;
""",
}

splash_imports = """import android.animation.Animator;
import android.animation.ObjectAnimator;
import android.animation.PropertyValuesHolder;
import android.animation.ValueAnimator;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.view.animation.BounceInterpolator;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.OvershootInterpolator;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
""" if use_splash else ''

splash_code = """        if (b == null) {
            final FrameLayout spl = new FrameLayout(this);
            spl.setBackgroundColor(Color.parseColor("@@BG@@"));
            spl.setClickable(true);
            float spD = getResources().getDisplayMetrics().density;
            spl.setPadding((int) (32 * spD), 0, (int) (32 * spD), 0);
            LinearLayout spCol = new LinearLayout(this);
            spCol.setOrientation(LinearLayout.VERTICAL);
            spCol.setGravity(Gravity.CENTER_HORIZONTAL);
            ImageView spLogo = new ImageView(this);
            spLogo.setImageResource(R.mipmap.ic_launcher);
            spLogo.setOutlineProvider(new ViewOutlineProvider() {
                @Override
                public void getOutline(View v, Outline o) {
                    o.setRoundRect(0, 0, v.getWidth(), v.getHeight(), v.getWidth() * 0.22f);
                }
            });
            spLogo.setClipToOutline(true);
            spCol.addView(spLogo, new LinearLayout.LayoutParams((int) (120 * spD), (int) (120 * spD)));
            TextView spText = new TextView(this);
            spText.setText(@@NAME@@);
            spText.setTextColor(Color.parseColor("@@FG@@"));
            spText.setTextSize(24);
            spText.setTypeface(Typeface.DEFAULT_BOLD);
            spText.setGravity(Gravity.CENTER);
            spText.setPadding(0, (int) (20 * spD), 0, 0);
            spCol.addView(spText, new LinearLayout.LayoutParams(-2, -2));
            spl.addView(spCol, new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER));
            addContentView(spl, new ViewGroup.LayoutParams(-1, -1));
            final Animator[] spKeep = new Animator[1];
@@ANIM@@            spText.setAlpha(0f);
            spText.setTranslationY(30 * spD);
            spText.animate().alpha(1f).translationY(0f).setStartDelay(500).setDuration(600).start();
            spl.postDelayed(() -> {
                if (spKeep[0] != null) spKeep[0].cancel();
                spl.animate().alpha(0f).setDuration(450).withEndAction(() -> {
                    ViewGroup par = (ViewGroup) spl.getParent();
                    if (par != null) par.removeView(spl);
                }).start();
            }, @@MS@@);
        }
""".replace('@@BG@@', sp_bg).replace('@@FG@@', sp_fg).replace('@@MS@@', str(sp_ms)).replace('@@ANIM@@', sp_anims[sp_style]).replace('@@NAME@@', json.dumps(name)) if use_splash else ''

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
SPLASH_IMPORTS
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
SPLASH_CODE        WebSettings s = web.getSettings();
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
""".replace('PKG', pkg).replace('TARGET', json.dumps(target)).replace('ADS_IMPORTS', ads_imports).replace('ADS_CODE', ads_code).replace('SPLASH_IMPORTS', splash_imports).replace('SPLASH_CODE', splash_code))

if c['mode'] == 'html':
    os.makedirs('app/src/main/assets', exist_ok=True)
    shutil.copy('index.html', 'app/src/main/assets/index.html')
if os.path.exists('icon.png'):
    os.makedirs('app/src/main/res/mipmap-xxxhdpi', exist_ok=True)
    shutil.copy('icon.png', 'app/src/main/res/mipmap-xxxhdpi/ic_launcher.png')
