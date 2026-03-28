package dev.mapanare.example

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Minimal Android app embedding a Mapanare-compiled shared library.
 *
 * Build the .so:
 *   mapanare build --target aarch64-linux-android --lib -o libmapanare_app.so app.mn
 *
 * Place libmapanare_app.so in app/src/main/jniLibs/arm64-v8a/
 */
class MainActivity : AppCompatActivity() {

    companion object {
        init {
            System.loadLibrary("mapanare_app")
        }
    }

    /** Declared in the Mapanare .mn source as a pub fn. */
    private external fun greet(name: String): String

    /** Example: agent-based background computation. */
    private external fun computeInBackground(input: Long): Long

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val tv = TextView(this).apply {
            text = greet("Android")
            textSize = 24f
        }
        setContentView(tv)
    }
}
