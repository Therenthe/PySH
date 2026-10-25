package ro.pysh.remote

/** ICO is a bounded container: PNG frames or bottom-up, uncompressed 32-bit DIB frames. */
internal object IcoArtwork {
    sealed interface Frame {
        data class Png(val bytes: ByteArray) : Frame
        data class Pixels(val width: Int, val height: Int, val argb: IntArray) : Frame
    }
    private data class Entry(val width: Int, val height: Int, val depth: Int, val offset: Int, val size: Int)
    private val signature = byteArrayOf(-119, 80, 78, 71, 13, 10, 26, 10)

    fun decode(bytes: ByteArray): Frame {
        require(bytes.size in 22..256 * 1024) { "invalid_ico" }
        require(u16(bytes, 0) == 0 && u16(bytes, 2) == 1) { "invalid_ico" }
        val count = u16(bytes, 4)
        require(count in 1..64 && 6 + count * 16 <= bytes.size) { "invalid_ico" }
        val directoryEnd = 6 + count * 16
        val entries = (0 until count).map { index ->
            val at = 6 + index * 16
            val size = u32(bytes, at + 8)
            val offset = u32(bytes, at + 12)
            require(bytes[at + 3].toInt() == 0 && u16(bytes, at + 4) in 0..1) { "invalid_ico" }
            require(size > 0 && offset >= directoryEnd && offset + size <= bytes.size) { "invalid_ico" }
            Entry((bytes[at].toInt() and 255).let { if (it == 0) 256 else it },
                (bytes[at + 1].toInt() and 255).let { if (it == 0) 256 else it },
                u16(bytes, at + 6), offset.toInt(), size.toInt())
        }.sortedWith(compareByDescending<Entry> { it.width * it.height }.thenByDescending { it.depth })
        for (entry in entries) {
            // Unsupported frames can coexist with a supported frame in the same icon.
            val frame = try { frame(bytes.copyOfRange(entry.offset, entry.offset + entry.size), entry) }
                catch (_: IllegalArgumentException) { null }
            if (frame != null) return frame
        }
        throw IllegalArgumentException("unsupported_ico")
    }

    private fun frame(data: ByteArray, entry: Entry): Frame {
        if (data.size >= 33 && signature.indices.all { data[it] == signature[it] }) {
            require(big32(data, 8) == 13L && data.copyOfRange(12, 16).contentEquals(byteArrayOf(73, 72, 68, 82)))
            require(big32(data, 16) == entry.width.toLong() && big32(data, 20) == entry.height.toLong())
            return Frame.Png(data)
        }
        require(data.size >= 40 && u32(data, 0) == 40L)
        require(u32(data, 4) == entry.width.toLong() && u32(data, 8) == entry.height.toLong() * 2)
        require(u16(data, 12) == 1 && u16(data, 14) == 32 && u32(data, 16) == 0L && u32(data, 32) == 0L)
        val colorSize = entry.width * entry.height * 4
        val maskStride = ((entry.width + 31) / 32) * 4
        val maskStart = 40 + colorSize
        require(maskStart + maskStride * entry.height <= data.size)
        val hasAlpha = (0 until entry.width * entry.height).any { data[40 + it * 4 + 3].toInt() != 0 }
        val pixels = IntArray(entry.width * entry.height)
        for (y in 0 until entry.height) for (x in 0 until entry.width) {
            val sourceY = entry.height - 1 - y
            val pixel = 40 + (sourceY * entry.width + x) * 4
            val masked = (data[maskStart + sourceY * maskStride + x / 8].toInt() and (128 ushr (x % 8))) != 0
            val alpha = if (masked) 0 else if (hasAlpha) data[pixel + 3].toInt() and 255 else 255
            pixels[y * entry.width + x] = (alpha shl 24) or ((data[pixel + 2].toInt() and 255) shl 16) or
                ((data[pixel + 1].toInt() and 255) shl 8) or (data[pixel].toInt() and 255)
        }
        return Frame.Pixels(entry.width, entry.height, pixels)
    }

    private fun u16(bytes: ByteArray, at: Int) = (bytes[at].toInt() and 255) or ((bytes[at + 1].toInt() and 255) shl 8)
    private fun u32(bytes: ByteArray, at: Int): Long = (0..3).fold(0L) { value, index -> value or ((bytes[at + index].toLong() and 255) shl (index * 8)) }
    private fun big32(bytes: ByteArray, at: Int): Long = (0..3).fold(0L) { value, index -> (value shl 8) or (bytes[at + index].toLong() and 255) }
}
