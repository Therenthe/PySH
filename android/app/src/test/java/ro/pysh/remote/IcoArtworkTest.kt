package ro.pysh.remote

import org.junit.Assert.*
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Base64

class IcoArtworkTest {
    private val png=Base64.getDecoder().decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5V8AAAAASUVORK5CYII=")
    private fun ico(frame:ByteArray,width:Int=1,height:Int=1):ByteArray = ByteBuffer.allocate(22+frame.size).order(ByteOrder.LITTLE_ENDIAN).apply {
        putShort(0);putShort(1);putShort(1);put(width.toByte());put(height.toByte());put(0);put(0)
        putShort(1);putShort(32);putInt(frame.size);putInt(22);put(frame)
    }.array()
    private fun dib(alpha:Boolean):ByteArray = ByteBuffer.allocate(64).order(ByteOrder.LITTLE_ENDIAN).apply {
        putInt(40);putInt(2);putInt(4);putShort(1);putShort(32);putInt(0);putInt(16)
        putInt(0);putInt(0);putInt(0);putInt(0)
        // Bottom row blue, white; top row red, green. Green is AND-masked.
        putInt(if(alpha) 0xff0000ff.toInt() else 0x000000ff)
        putInt(if(alpha) 0xffffffff.toInt() else 0x00ffffff)
        putInt(if(alpha) 0x80ff0000.toInt() else 0x00ff0000)
        putInt(if(alpha) 0xff00ff00.toInt() else 0x0000ff00)
        putInt(0);putInt(0x40)
    }.array()
    @Test fun acceptsPngFrameAndPreservesBytes() {
        assertArrayEquals(png,(IcoArtwork.decode(ico(png)) as IcoArtwork.Frame.Png).bytes)
    }
    @Test fun rendersBottomUpPixelsWithAlphaAndMask() {
        val frame=IcoArtwork.decode(ico(dib(true),2,2)) as IcoArtwork.Frame.Pixels
        assertEquals(2,frame.width);assertEquals(2,frame.height)
        assertArrayEquals(intArrayOf(0x80ff0000.toInt(),0x0000ff00,0xff0000ff.toInt(),0xffffffff.toInt()),frame.argb)
    }
    @Test fun legacyZeroAlphaUsesAndTransparency() {
        val frame=IcoArtwork.decode(ico(dib(false),2,2)) as IcoArtwork.Frame.Pixels
        assertArrayEquals(intArrayOf(0xffff0000.toInt(),0x0000ff00,0xff0000ff.toInt(),0xffffffff.toInt()),frame.argb)
    }
    @Test fun rejectsInvalidDirectoriesAndContainerBounds() {
        val valid=ico(png)
        fun rejects(value:ByteArray)=assertThrows(IllegalArgumentException::class.java) { IcoArtwork.decode(value) }
        rejects(ByteArray(5));rejects(ByteArray(256*1024+1))
        rejects(valid.copyOf().apply { this[2]=2 }) // CUR is not ICO.
        rejects(valid.copyOf().apply { this[4]=65 })
        rejects(valid.copyOf().apply { this[9]=1 }) // Directory reserved byte.
        rejects(valid.copyOf().apply { (18..21).forEach { this[it]=0xff.toByte() } })
        rejects(valid.copyOf().apply { (14..17).forEach { this[it]=0xff.toByte() } })
        rejects(valid.copyOf().apply { this[18]=6 }) // Frame cannot overlap directory.
        rejects(valid.copyOf(valid.size-1))
    }
    @Test fun rejectsUnsupportedOrInconsistentFrameHeaders() {
        fun rejects(frame:ByteArray,width:Int=2,height:Int=2)=assertThrows(IllegalArgumentException::class.java) { IcoArtwork.decode(ico(frame,width,height)) }
        rejects(dib(true).copyOf(60)) // Incomplete AND mask.
        rejects(dib(true).apply { this[14]=24 })
        rejects(dib(true).apply { this[16]=1 }) // Compressed DIB.
        rejects(dib(true).apply { this[4]=3 })
        rejects(dib(true).apply { this[8]=2 }) // Height must include both masks.
        rejects(dib(true).apply { this[35]=1 }) // Color table unsupported for 32-bit frame.
        rejects(png,2,2)
        rejects(png.copyOf().apply { this[16]=1 },1,1) // Huge PNG width does not match bounded directory.
    }
    @Test fun choosesSupportedFrameWhenLargerFrameIsUnsupported() {
        val unsupported=dib(true).apply { this[14]=24 }
        val bytes=ByteBuffer.allocate(38+unsupported.size+png.size).order(ByteOrder.LITTLE_ENDIAN).apply {
            putShort(0);putShort(1);putShort(2)
            put(2);put(2);put(0);put(0);putShort(1);putShort(24);putInt(unsupported.size);putInt(38)
            put(1);put(1);put(0);put(0);putShort(1);putShort(32);putInt(png.size);putInt(38+unsupported.size)
            put(unsupported);put(png)
        }.array()
        assertTrue(IcoArtwork.decode(bytes) is IcoArtwork.Frame.Png)
    }
}
