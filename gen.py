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
sp_bg = sp.get('bg') if re.fullmatch(r'#[0-9a-fA-F]{6}', str(sp.get('bg', ''))) else '#1f7a4d'
try:
    sp_ms = min(max(int(sp.get('ms', 3000)), 1000), 6000)
except (TypeError, ValueError):
    sp_ms = 3000
sp_lum = 0.299 * int(sp_bg[1:3], 16) + 0.587 * int(sp_bg[3:5], 16) + 0.114 * int(sp_bg[5:7], 16)
sp_fg = '#000000' if sp_lum > 160 else '#FFFFFF'

SP_PROPS = ('alpha', 'scaleX', 'scaleY', 'translationX', 'translationY', 'rotation', 'rotationX', 'rotationY')
SP_INTERP = {'linear': 'LinearInterpolator', 'accel': 'AccelerateInterpolator', 'decel': 'DecelerateInterpolator',
             'accdec': 'AccelerateDecelerateInterpolator', 'overshoot': 'OvershootInterpolator',
             'anticipate': 'AnticipateInterpolator', 'pop': 'AnticipateOvershootInterpolator', 'bounce': 'BounceInterpolator'}
SP_FONTS = ('sans-serif', 'serif', 'monospace', 'cursive', 'casual', 'sans-serif-condensed', 'sans-serif-light', 'sans-serif-thin', 'sans-serif-black')
IND = '            '

def sp_num(k, v):
    n = max(-5000.0, min(5000.0, float(v)))
    return str(n) + 'f' + (' * spD' if k.startswith('translation') else '')

def sp_one(a, var, tgt, loop):
    hs, init = [], ''
    for k, vals in (a.get('p') or {}).items():
        if k not in SP_PROPS or not isinstance(vals, list) or len(vals) < 2:
            continue
        nums = [sp_num(k, v) for v in vals[:12]]
        hs.append('PropertyValuesHolder.ofFloat("' + k + '", ' + ', '.join(nums) + ')')
        init += IND + tgt + '.set' + k[0].upper() + k[1:] + '(' + nums[0] + ');\n'
    if not hs:
        return ''
    itp = SP_INTERP.get(a.get('i'), 'LinearInterpolator')
    dur = max(100, min(5000, int(a.get('d', 800))))
    delay = max(0, min(6000, int(a.get('delay', 0))))
    code = '' if loop else init
    code += IND + 'ObjectAnimator ' + var + ' = ObjectAnimator.ofPropertyValuesHolder(' + tgt + ', ' + ', '.join(hs) + ');\n'
    code += IND + var + '.setDuration(' + str(dur) + ');\n'
    code += IND + var + '.setInterpolator(new android.view.animation.' + itp + '());\n'
    if delay:
        code += IND + var + '.setStartDelay(' + str(delay) + ');\n'
    if loop:
        code += IND + var + '.setRepeatCount(ValueAnimator.INFINITE);\n'
        code += IND + var + '.setRepeatMode(ValueAnimator.' + ('RESTART' if a.get('mode') == 'restart' else 'REVERSE') + ');\n'
    return code + IND + var + '.start();\n'

def sp_anim_code(a, tgt, pre, idx):
    if not isinstance(a, dict):
        return ''
    code = sp_one(a, pre + '1', tgt, False)
    if code:
        code += IND + 'spKeep[' + str(idx) + '] = ' + pre + '1;\n'
    if isinstance(a.get('loop'), dict):
        lp = sp_one(a['loop'], pre + '2', tgt, True)
        if lp:
            code += lp + IND + 'spKeep[' + str(idx + 1) + '] = ' + pre + '2;\n'
    return code

def sp_text_anim(a, text):
    if isinstance(a, dict) and a.get('special') == 'typewriter':
        dur = max(300, len(text) * 90)
        return (IND + 'final String spFull = @@NAME@@;\n' + IND + 'spText.setText("");\n'
                + IND + 'ValueAnimator spTw = ValueAnimator.ofInt(0, spFull.length());\n'
                + IND + 'spTw.setDuration(' + str(dur) + ');\n' + IND + 'spTw.setStartDelay(500);\n'
                + IND + 'spTw.setInterpolator(new android.view.animation.LinearInterpolator());\n'
                + IND + 'spTw.addUpdateListener(va -> spText.setText(spFull.substring(0, (Integer) va.getAnimatedValue())));\n'
                + IND + 'spTw.start();\n' + IND + 'spKeep[2] = spTw;\n')
    return sp_anim_code(a, 'spText', 'spT', 2)

tx = sp.get('text') if isinstance(sp.get('text'), dict) else {}
tx_val = str(tx.get('value') or name)[:60]
if tx.get('case') == 'upper':
    tx_val = tx_val.upper()
elif tx.get('case') == 'lower':
    tx_val = tx_val.lower()
tx_col = tx.get('color') if re.fullmatch(r'#[0-9a-fA-F]{6}', str(tx.get('color', ''))) else sp_fg
tx_font = tx.get('font') if tx.get('font') in SP_FONTS else 'sans-serif'
tx_style = {'normal': 'NORMAL', 'bold': 'BOLD', 'italic': 'ITALIC', 'bolditalic': 'BOLD_ITALIC'}.get(tx.get('weight'), 'BOLD')
try:
    tx_size = min(max(int(tx.get('size', 24)), 12), 60)
    tx_sp = min(max(float(tx.get('spacing', 0)), 0.0), 0.5)
except (TypeError, ValueError):
    tx_size, tx_sp = 24, 0.0
tx_extra = ''
if tx_sp:
    tx_extra += IND + 'spText.setLetterSpacing(' + str(tx_sp) + 'f);\n'
if tx.get('glow'):
    tx_extra += IND + 'spText.setShadowLayer(12 * spD, 0, 0, Color.parseColor("#99' + tx_col[1:] + '"));\n'
if tx.get('show', True) is False:
    tx_extra += IND + 'spText.setVisibility(View.GONE);\n'
tx_anim = sp_text_anim(tx.get('anim') if tx.get('anim') else {'d': 600, 'i': 'accdec', 'delay': 500, 'p': {'alpha': [0, 1], 'translationY': [30, 0]}}, tx_val)

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
            spText.setTextColor(Color.parseColor("@@TXCOL@@"));
            spText.setTextSize(@@SIZE@@);
            spText.setTypeface(Typeface.create("@@FONT@@", Typeface.@@TSTYLE@@));
            spText.setGravity(Gravity.CENTER);
            spText.setPadding(0, (int) (20 * spD), 0, 0);
@@TEXTRA@@            spCol.addView(spText, new LinearLayout.LayoutParams(-2, -2));
            spl.addView(spCol, new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER));
            addContentView(spl, new ViewGroup.LayoutParams(-1, -1));
            final Animator[] spKeep = new Animator[4];
            spLogo.setCameraDistance(8000 * spD);
@@ANIM@@            spText.setCameraDistance(8000 * spD);
@@TANIM@@            spl.postDelayed(() -> {
                for (Animator x : spKeep) if (x != null) x.cancel();
                spl.animate().alpha(0f).setDuration(450).withEndAction(() -> {
                    ViewGroup par = (ViewGroup) spl.getParent();
                    if (par != null) par.removeView(spl);
                }).start();
            }, @@MS@@);
        }
""".replace('@@BG@@', sp_bg).replace('@@FG@@', sp_fg).replace('@@MS@@', str(sp_ms)).replace('@@ANIM@@', sp_anim_code(sp.get('anim'), 'spLogo', 'spA', 0)).replace('@@TANIM@@', tx_anim).replace('@@TEXTRA@@', tx_extra).replace('@@TXCOL@@', tx_col).replace('@@SIZE@@', str(tx_size)).replace('@@FONT@@', tx_font).replace('@@TSTYLE@@', tx_style).replace('@@NAME@@', json.dumps(tx_val)) if use_splash else ''

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
