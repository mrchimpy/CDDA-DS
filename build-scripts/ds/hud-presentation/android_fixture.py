"""Tiny host-only Android substitutes: test call routing, NOT Android rendering/focus."""
from pathlib import Path

SOURCES = {
'android/annotation/TargetApi.java': '''package android.annotation;
public @interface TargetApi { int value(); }''',
'android/R.java': '''package android;
public final class R {
 public static final class style { public static final int Theme_Material_NoActionBar=1; }
 public static final class attr { public static final int progressBarStyleHorizontal=2; }
}''',
'android/content/res/AssetManager.java': '''package android.content.res;
public class AssetManager {
 public boolean failPrimary, failFallback, failModern, failBuilder;
 public int modernCalls, legacyCalls;
}''',
'android/content/res/Resources.java': '''package android.content.res;
public class Resources { public android.util.DisplayMetrics getDisplayMetrics() {
 return new android.util.DisplayMetrics(); } }''',
'android/content/Context.java': '''package android.content;
public class Context {
 public static final String DISPLAY_SERVICE="display";
 public final android.content.res.AssetManager assets = new android.content.res.AssetManager();
 public android.content.res.AssetManager getAssets() { return assets; }
 public android.content.res.Resources getResources() { return new android.content.res.Resources(); }
 public Object getSystemService(String s) { return new android.hardware.display.DisplayManager(); }
}''',
'android/content/DialogInterface.java': '''package android.content;
public interface DialogInterface { interface OnDismissListener { void onDismiss(DialogInterface d); } }''',
'android/util/DisplayMetrics.java': '''package android.util;
public class DisplayMetrics { public float density=1.0f; }''',
'android/util/Log.java': '''package android.util;
public class Log {
 public static int warnings;
 public static int i(String tag,String message) { return 0; }
 public static int w(String tag,String message,Throwable error) { warnings++; return 0; }
 public static int e(String tag,String message,Throwable error) { return 0; }
}''',
'android/graphics/Color.java': '''package android.graphics;
public class Color { public static final int WHITE=0xffffffff, BLACK=0xff000000;
 public static int rgb(int r,int g,int b) { return BLACK | r<<16 | g<<8 | b; } }''',
'android/graphics/drawable/ColorDrawable.java': '''package android.graphics.drawable;
public class ColorDrawable { public final int color; public ColorDrawable(int c) { color=c; } }''',
'android/graphics/fonts/FontStyle.java': '''package android.graphics.fonts;
public class FontStyle {}''',
'android/graphics/fonts/Font.java': '''package android.graphics.fonts;
import android.content.res.AssetManager;
public class Font {
 public final String path; public final AssetManager assets;
 private Font(AssetManager a,String p) { assets=a; path=p; }
 public FontStyle getStyle() { return new FontStyle(); }
 public static class Builder {
  private final AssetManager assets; private final String path;
  public Builder(AssetManager a,String p) { assets=a; path=p; }
  public Font build() throws java.io.IOException {
   assets.modernCalls++;
   if(assets.failModern || (path.contains("Terminus") ? assets.failPrimary : assets.failFallback))
    throw new java.io.IOException("Injected font failure");
   return new Font(assets,path);
  }
 }
}''',
'android/graphics/fonts/FontFamily.java': '''package android.graphics.fonts;
public class FontFamily {
 public final Font font; private FontFamily(Font f) { font=f; }
 public static class Builder { private final Font font;
  public Builder(Font f) { font=f; } public FontFamily build() { return new FontFamily(font); }
 }
}''',
'android/graphics/Typeface.java': '''package android.graphics;
import android.content.res.AssetManager;
import android.graphics.fonts.*;
public class Typeface {
 public final String primary; public String fallback="",system="";
 public static final Typeface MONOSPACE=new Typeface("android-monospace");
 private Typeface(String p) { primary=p; }
 public static Typeface createFromAsset(AssetManager a,String p) {
  a.legacyCalls++; if(a.failPrimary) throw new RuntimeException("Injected legacy failure");
  return new Typeface(p);
 }
 public static class CustomFallbackBuilder {
  private final FontFamily family; private final Typeface result;
  public CustomFallbackBuilder(FontFamily f) { family=f; result=new Typeface(f.font.path); }
  public CustomFallbackBuilder addCustomFallback(FontFamily f) { result.fallback=f.font.path; return this; }
  public CustomFallbackBuilder setStyle(FontStyle s) { return this; }
  public CustomFallbackBuilder setSystemFallback(String name) { result.system=name; return this; }
  public Typeface build() {
   if(family.font.assets.failBuilder) throw new IllegalArgumentException("Injected build failure");
   return result;
  }
 }
}''',
'android/os/Build.java': '''package android.os;
public class Build { public static class VERSION { public static int SDK_INT=35; } }''',
'android/os/Bundle.java': '''package android.os; public class Bundle {}''',
'android/os/Looper.java': '''package android.os;
public class Looper { public static Looper getMainLooper() { return new Looper(); } }''',
'android/os/Handler.java': '''package android.os;
public class Handler { public Handler(Looper l) {} public void post(Runnable r) {}
 public void postDelayed(Runnable r,long d) {} public void removeCallbacks(Runnable r) {} }''',
'android/view/Display.java': '''package android.view;
public class Display { public static final int STATE_OFF=1;
 public int getDisplayId(){return 1;} public String getName(){return "host substitute";}
 public int getFlags(){return 0;} public int getState(){return 2;} public boolean isValid(){return true;}
}''',
'android/view/MotionEvent.java': '''package android.view; public class MotionEvent {}''',
'android/view/View.java': '''package android.view;
import android.content.Context;
public class View {
 public static final int VISIBLE=0, GONE=8;
 public int background=0x11223344, visibility=VISIBLE; public boolean focusable;
 public int[] padding; public final Context context;
 public View(Context c){context=c;} public void setBackgroundColor(int c){background=c;}
 public void setFocusable(boolean f){focusable=f;} public void setVisibility(int v){visibility=v;}
 public void setPadding(int a,int b,int c,int d){padding=new int[]{a,b,c,d};}
 public void setOnTouchListener(OnTouchListener l){} public Display getDisplay(){return new Display();}
 public interface OnTouchListener { boolean onTouch(View v,MotionEvent event); }
}''',
'android/view/ViewGroup.java': '''package android.view;
import android.content.Context; import java.util.*;
public class ViewGroup extends View {
 public static final int FOCUS_BLOCK_DESCENDANTS=0x60000; public int descendants;
 public final List<View> children=new ArrayList<>();
 public ViewGroup(Context c){super(c);} public void addView(View v){children.add(v);}
 public void addView(View v,LayoutParams p){children.add(v);}
 public void setDescendantFocusability(int v){descendants=v;}
 public static class LayoutParams {
  public static final int MATCH_PARENT=-1, WRAP_CONTENT=-2; public int width,height;
  public LayoutParams(int w,int h){width=w;height=h;}
 }
}''',
'android/view/Gravity.java': '''package android.view;
public class Gravity { public static final int CENTER_VERTICAL=16; }''',
'android/view/Window.java': '''package android.view;
import android.graphics.drawable.ColorDrawable;
public class Window {
 public int flags; public ColorDrawable background; public int width,height;
 public void addFlags(int f){flags|=f;} public void clearFlags(int f){flags&=~f;}
 public void setBackgroundDrawable(ColorDrawable d){background=d;}
 public void setLayout(int w,int h){width=w;height=h;}
 public View getDecorView(){return new View(new android.content.Context());}
}''',
'android/view/WindowManager.java': '''package android.view;
public class WindowManager {
 public Display getDefaultDisplay(){return new Display();}
 public static class LayoutParams extends ViewGroup.LayoutParams {
  public static final int FLAG_NOT_FOCUSABLE=8, FLAG_DIM_BEHIND=2;
  public LayoutParams(int w,int h){super(w,h);}
 }
}''',
'android/hardware/display/DisplayManager.java': '''package android.hardware.display;
import android.view.Display; import android.os.Handler;
public class DisplayManager {
 public static final String DISPLAY_CATEGORY_PRESENTATION="presentation";
 public void registerDisplayListener(DisplayListener l,Handler h){}
 public void unregisterDisplayListener(DisplayListener l){}
 public Display[] getDisplays(){return new Display[]{new Display()};}
 public Display[] getDisplays(String category){return getDisplays();}
 public interface DisplayListener { void onDisplayAdded(int id); void onDisplayRemoved(int id); void onDisplayChanged(int id); }
}''',
'android/app/Activity.java': '''package android.app;
public class Activity extends android.content.Context {
 public boolean isFinishing(){return false;} public android.view.Window getWindow(){return new android.view.Window();}
 public android.view.WindowManager getWindowManager(){return new android.view.WindowManager();}
 public java.io.File getExternalFilesDir(String s){return null;}
}''',
'android/app/Presentation.java': '''package android.app;
import android.content.*; import android.view.*; import android.os.Bundle;
public class Presentation implements DialogInterface {
 private final Context context; public final Window window=new Window(); public View content;
 public Presentation(Context c,Display d,int theme){context=c;}
 public Context getContext(){return context;} public Window getWindow(){return window;}
 public void setCancelable(boolean value){} protected void onCreate(Bundle state){}
 public void setContentView(View v){content=v;} public void setOnDismissListener(OnDismissListener l){}
 public void show(){} public void dismiss(){} public boolean isShowing(){return true;}
 public Display getDisplay(){return new Display();}
}''',
'android/widget/LinearLayout.java': '''package android.widget;
import android.view.*; import android.content.Context;
public class LinearLayout extends ViewGroup {
 public static final int VERTICAL=1; public LinearLayout(Context c){super(c);}
 public void setOrientation(int i){} public void setGravity(int g){}
 public static class LayoutParams extends ViewGroup.LayoutParams {
  public float weight; public int rightMargin;
  public LayoutParams(int w,int h){super(w,h);} public LayoutParams(int w,int h,float f){super(w,h);weight=f;}
 }
}''',
'android/widget/ScrollView.java': '''package android.widget;
import android.view.*; import android.content.Context;
public class ScrollView extends ViewGroup { public boolean fill;
 public ScrollView(Context c){super(c);} public void setFillViewport(boolean f){fill=f;}
}''',
'android/widget/TextView.java': '''package android.widget;
import android.view.*; import android.content.Context; import android.graphics.Typeface;
public class TextView extends View {
 public String text="",features=""; public Typeface face; public float size,spacing; public int color;
 public TextView(Context c){super(c);} public void setText(String t){text=t;}
 public void setTextSize(float s){size=s;} public void setTextColor(int c){color=c;}
 public void setTypeface(Typeface f){face=f;} public void setLetterSpacing(float s){spacing=s;}
 public void setFontFeatureSettings(String f){features=f;}
}''',
'android/widget/ProgressBar.java': '''package android.widget;
import android.view.*; import android.content.Context;
public class ProgressBar extends View {
 public int maximum,progress; public ProgressBar(Context c,Object attrs,int style){super(c);}
 public void setMax(int m){maximum=m;} public void setProgress(int p){progress=p;}
}''',
'android/widget/Toast.java': '''package android.widget;
import android.content.Context;
public class Toast { public static final int LENGTH_LONG=1;
 public static Toast makeText(Context c,String s,int length){return new Toast();} public void show(){} }
''',
}


def write_stubs(root: Path) -> list[Path]:
    paths = []
    for name, source in SOURCES.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(source + '\n', encoding='utf-8')
        paths.append(p)
    return paths
