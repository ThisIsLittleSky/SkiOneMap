package com.ski.monitor.controller;

import org.springframework.core.io.AbstractResource;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * 支持 HTTP Range 的文件资源，从指定字节偏移量开始读取指定长度。
 */
public class RangeResource extends AbstractResource {

    private final Path filePath;
    private final long offset;
    private final long length;

    public RangeResource(Path filePath, long offset, long length) {
        this.filePath = filePath;
        this.offset = offset;
        this.length = length;
    }

    @Override
    public String getDescription() {
        return "Range resource [" + filePath + "] offset=" + offset + " length=" + length;
    }

    @Override
    public InputStream getInputStream() throws IOException {
        InputStream is = Files.newInputStream(filePath);
        long skipped = is.skip(offset);
        if (skipped < offset) {
            is.close();
            throw new IOException("Could not skip to offset " + offset);
        }
        return new BoundedInputStream(is, length);
    }

    @Override
    public long contentLength() {
        return length;
    }

    /** 包装 InputStream，限制最多读取 maxBytes 字节。 */
    private static class BoundedInputStream extends InputStream {
        private final InputStream delegate;
        private long remaining;

        BoundedInputStream(InputStream delegate, long maxBytes) {
            this.delegate = delegate;
            this.remaining = maxBytes;
        }

        @Override
        public int read() throws IOException {
            if (remaining <= 0) return -1;
            int b = delegate.read();
            if (b != -1) remaining--;
            return b;
        }

        @Override
        public int read(byte[] buf, int off, int len) throws IOException {
            if (remaining <= 0) return -1;
            int toRead = (int) Math.min(len, remaining);
            int n = delegate.read(buf, off, toRead);
            if (n > 0) remaining -= n;
            return n;
        }

        @Override
        public void close() throws IOException {
            delegate.close();
        }
    }
}
