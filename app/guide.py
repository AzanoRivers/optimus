from fastapi.responses import HTMLResponse

_GUIDE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Optimus API — Guide</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0d1117; color: #c9d1d9; line-height: 1.6;
    }
    a { color: #58a6ff; text-decoration: none; }
    a:hover { text-decoration: underline; }

    .header { 
      background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
      border-bottom: 1px solid #30363d;
      padding: 2.5rem 2rem 2rem;
      text-align: center;
    }
    .header h1 { font-size: 2rem; color: #f0f6fc; letter-spacing: -0.5px; }
    .header p  { margin-top: 0.4rem; color: #8b949e; font-size: 0.95rem; }
    .header-links {
      margin-top: 1rem;
      display: flex; gap: 1.2rem; justify-content: center; flex-wrap: wrap;
    }
    .header-links a {
      color: #8b949e; font-size: 0.8rem; text-decoration: none;
      display: flex; align-items: center; gap: 0.3rem;
      transition: color 0.15s;
    }
    .header-links a:hover { color: #58a6ff; }
    .badge {
      display: inline-block; margin-top: 0.8rem;
      background: #238636; color: #fff; font-size: 0.75rem;
      padding: 0.2rem 0.7rem; border-radius: 20px; font-weight: 600;
    }

    .container { max-width: 860px; margin: 0 auto; padding: 2rem 1rem 4rem; }

    /* lang cards */
    .lang-picker {
      display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
      margin-bottom: 2.5rem;
    }
    .lang-card {
      display: flex; align-items: center; gap: 0.75rem;
      background: #161b22; border: 2px solid #30363d; border-radius: 12px;
      padding: 0.9rem 1.5rem; cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
      user-select: none; flex: 1 1 140px; max-width: 220px;
    }
    .lang-card:hover { border-color: #58a6ff; background: #1c2333; }
    .lang-card.active {
      border-color: #58a6ff; background: #1c2333;
      box-shadow: 0 0 0 3px rgba(88,166,255,.15);
    }
    .lang-card .flag  { font-size: 1.8rem; line-height: 1; }
    .lang-card .label { display: flex; flex-direction: column; }
    .lang-card .label strong { font-size: 0.95rem; color: #f0f6fc; }
    .lang-card .label span   { font-size: 0.75rem; color: #8b949e; }

    /* content toggle */
    .lang-content         { display: none; }
    .lang-content.visible { display: block; }

    /* TOC */
    .toc {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 1.25rem 1.5rem; margin-bottom: 2.5rem;
    }
    .toc h2 {
      font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;
      color: #8b949e; margin-bottom: 0.75rem;
    }
    .toc ol { padding-left: 1.25rem; }
    .toc li { margin: 0.25rem 0; font-size: 0.9rem; }

    section { margin-bottom: 2.5rem; }
    h2 {
      font-size: 1.2rem; color: #f0f6fc;
      border-bottom: 1px solid #21262d;
      padding-bottom: 0.4rem; margin-bottom: 1rem;
    }
    h3 { font-size: 1rem; color: #e6edf3; margin: 1.25rem 0 0.5rem; }
    p, li { font-size: 0.9rem; color: #c9d1d9; }
    ul, ol { padding-left: 1.25rem; margin-top: 0.4rem; }
    li { margin: 0.2rem 0; }

    code {
      background: #161b22; border: 1px solid #30363d;
      border-radius: 4px; padding: 0.1rem 0.4rem;
      font-family: "SFMono-Regular", Consolas, monospace; font-size: 0.82rem;
      color: #e6edf3; word-break: break-word;
    }
    pre {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 1rem 1.25rem; overflow-x: auto; margin-top: 0.75rem;
    }
    pre code {
      background: none; border: none; padding: 0; word-break: normal;
      font-size: 0.82rem; color: #e6edf3; line-height: 1.7;
    }

    .endpoint {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 1rem 1.25rem; margin-bottom: 1rem;
    }
    .endpoint-header {
      display: flex; align-items: center; flex-wrap: wrap; gap: 0.4rem;
    }
    .method {
      display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px;
      font-size: 0.75rem; font-weight: 700; margin-right: 0.25rem;
      font-family: monospace; white-space: nowrap;
    }
    .get    { background: #0e4429; color: #3fb950; }
    .post   { background: #1f2d5a; color: #79c0ff; }
    .delete { background: #4a1010; color: #ff7b72; }
    .path { font-family: monospace; font-size: 0.85rem; color: #f0f6fc; word-break: break-all; }
    .auth-badge {
      margin-left: auto; font-size: 0.72rem; padding: 0.15rem 0.5rem;
      border-radius: 12px; border: 1px solid #30363d; color: #8b949e;
      white-space: nowrap;
    }
    .auth-badge.required { border-color: #f0883e; color: #f0883e; }

    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 0.75rem; }
    table {
      width: 100%; border-collapse: collapse; font-size: 0.85rem;
      min-width: 400px;
    }
    th {
      background: #161b22; color: #8b949e; text-align: left;
      padding: 0.5rem 0.75rem; border-bottom: 1px solid #30363d;
      font-weight: 600; font-size: 0.78rem; text-transform: uppercase;
      white-space: nowrap;
    }
    td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; }
    tr:last-child td { border-bottom: none; }
    td code { font-size: 0.78rem; }
    td:first-child { white-space: nowrap; }

    .status-row td:first-child { font-family: monospace; font-weight: 700; }
    .s200 { color: #3fb950; }
    .s206 { color: #79c0ff; }
    .s401 { color: #f0883e; }
    .s408 { color: #f0883e; }
    .s422 { color: #d2a8ff; }
    .s501 { color: #8b949e; }
    .s503 { color: #f0883e; }

    .note {
      background: #1f2d5a; border-left: 3px solid #79c0ff;
      border-radius: 0 6px 6px 0;
      padding: 0.75rem 1rem; font-size: 0.85rem; margin-top: 0.75rem;
    }

    @media (max-width: 600px) {
      .header h1 { font-size: 1.4rem; }
      .header p  { font-size: 0.85rem; }
      .header-links { gap: 0.8rem; }
      .container { padding: 1.25rem 0.75rem 3rem; }
      .lang-card { padding: 0.75rem 1rem; flex: 1 1 100%; max-width: 100%; }
      .lang-picker { flex-direction: column; align-items: stretch; }
      .endpoint-header { gap: 0.3rem; }
      .auth-badge { margin-left: 0; }
      pre { padding: 0.75rem; }
      th, td { padding: 0.4rem 0.5rem; font-size: 0.78rem; }
    }
  </style>
</head>
<body>

<div class="header">
  <h1>&#x26A1; Optimus API</h1>
  <p>Media compression service &middot; REST API reference</p>
  <span class="badge">v1</span>
  <div class="header-links">
    <a href="https://www.azanorivers.com/" target="_blank" rel="noopener">&#x1F464; AzanoRivers</a>
    <a href="https://github.com/azanoRivers" target="_blank" rel="noopener">&#x1F4BB; GitHub</a>
    <a href="https://www.azanolabs.com/" target="_blank" rel="noopener">&#x1F9EA; AzanoLabs</a>
  </div>
</div>

<div class="container">

  <!-- lang picker -->
  <div class="lang-picker">
    <div class="lang-card active" onclick="switchLang('en', this)">
      <span class="flag">&#x1F1FA;&#x1F1F8;</span>
      <div class="label">
        <strong>English</strong>
        <span>Documentation in English</span>
      </div>
    </div>
    <div class="lang-card" onclick="switchLang('es', this)">
      <span class="flag">&#x1F1EA;&#x1F1F8;</span>
      <div class="label">
        <strong>Espa&ntilde;ol</strong>
        <span>Documentaci&oacute;n en espa&ntilde;ol</span>
      </div>
    </div>
  </div>

  <!-- ==================== ENGLISH ==================== -->
  <div id="lang-en" class="lang-content visible">

    <div class="toc">
      <h2>Contents</h2>
      <ol>
        <li><a href="#en-auth">Authentication</a></li>
        <li><a href="#en-endpoints">Endpoints</a></li>
        <li><a href="#en-params">Parameters</a></li>
        <li><a href="#en-limits">Limits</a></li>
        <li><a href="#en-response">Response &amp; Headers</a></li>
        <li><a href="#en-status">HTTP Status Codes</a></li>
        <li><a href="#en-examples">curl Examples</a></li>
        <li><a href="#en-video">Video Compression</a></li>
      </ol>
    </div>

    <section id="en-auth">
      <h2>Authentication</h2>
      <p>Endpoints under <code>/api/v1/</code> support two authentication methods:</p>
      <h3>Master API Key (server-to-server)</h3>
      <p>Used by your backend (e.g. a Vercel server function). <strong>Never expose this key in the browser.</strong></p>
      <pre><code>X-API-Key: your-secret-key</code></pre>
      <h3>Session Token (browser direct calls)</h3>
      <p>Short-lived token (2&nbsp;h TTL) obtained server-side via <code>POST /api/v1/auth/session-token</code> and forwarded to the browser. Allows the browser to call the VPS directly without exposing the master key.</p>
      <pre><code>X-Session-Token: &lt;token&gt;</code></pre>
      <h4>Token lifecycle</h4>
      <ul>
        <li>Valid for <strong>2 hours</strong> from the moment of issuance</li>
        <li>Renew proactively ~12 min before expiry to avoid mid-upload failures</li>
        <li>If a token expires during an upload, cancel the job (<code>DELETE /upload/{upload_id}</code>) and retry with a fresh token</li>
        <li>Tokens live in server memory, a VPS restart invalidates all active tokens</li>
      </ul>
      <p>Requests without a valid key or token return <code>401 Unauthorized</code>. The <code>GET /guide</code> and <code>GET /guide-ai</code> endpoints are public &middot; no authentication required.</p>
    </section>

    <section id="en-endpoints">
      <h2>Endpoints</h2>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/guide</span>
          <span class="auth-badge">public</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">This page. HTML API reference guide.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/guide-ai</span>
          <span class="auth-badge">public</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Machine-readable JSON reference optimized for AI agents (LLMs, LangChain, MCP, etc.). Same content as this guide but structured for programmatic consumption, no HTML parsing required.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/auth/session-token</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Exchange the master API key for a short-lived session token (2&nbsp;h TTL). Call this server-side and forward the token to the browser. The browser then authenticates with <code>X-Session-Token</code> to call the VPS directly. Body: none. Response: <code>{ token, expires_in }</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/images/compress</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Compress one or more images. Accepts <code>multipart/form-data</code>. Returns a single compressed image or a ZIP archive.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/init</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Start a video upload session. Body: <code>{filename, total_size, total_chunks}</code>. Returns <code>upload_id</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/chunk</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Upload one video chunk (max 90 MB). Form-data: <code>upload_id</code>, <code>chunk_index</code> (0-based), <code>chunk</code> (file). Repeat sequentially.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/finalize</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Signal that all chunks are uploaded. Body: <code>{upload_id}</code>. Returns <code>job_id</code> with <code>status: queued</code>. Responds <code>503</code> if the queue is full.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/api/v1/media/videos/status/{job_id}</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Poll compression status. Returns <code>status</code>, <code>progress_pct</code>, <code>input_size</code>, <code>output_size</code>, <code>reduction_pct</code>, <code>error_msg</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/api/v1/media/videos/download/{job_id}</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Download the compressed video. Only available when <code>status: done</code>. File is deleted from the server once the transfer completes.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method delete">DELETE</span>
          <span class="path">/api/v1/media/videos/upload/{upload_id}</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Cancel and clean up a job at any stage (uploading, queued, processing, done). Kills FFmpeg if running, deletes all temporary files. Returns <code>{cancelled: true, job_id}</code>. Returns <code>404</code> if already gone.</p>
      </div>
    </section>

    <section id="en-params">
      <h2>Parameters &middot; POST /api/v1/media/images/compress</h2>
      <p>The <code>files</code> field must be sent as <code>multipart/form-data</code>. The optional parameters <code>out</code>, <code>size</code>, and <code>lossy</code> are accepted both as form fields <strong>or as URL query params</strong>. Using query params in the URL is recommended to avoid multipart parsing issues with some clients (e.g. Postman).</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>files</code></td><td>file(s)</td><td>Yes</td><td>&middot;</td><td>1&ndash;10 images. Allowed: <code>.jpg</code> <code>.jpeg</code> <code>.png</code> <code>.webp</code></td></tr>
          <tr><td><code>out</code></td><td>string</td><td>No</td><td>keep original</td><td>Output format: <code>jpg</code>, <code>webp</code>, or <code>png</code>. Converts all images to the specified format.</td></tr>
          <tr><td><code>size</code></td><td>integer</td><td>No</td><td>no resize</td><td>Max pixels on longest side (1&ndash;8000). Aspect ratio preserved. Never upscales.</td></tr>
          <tr><td><code>lossy</code></td><td>boolean</td><td>No</td><td>false</td><td>Lossy PNG compression via color quantization (pngquant-style, 256 colors). Only applies when output format is PNG. Achieves ~80% size reduction. Ignored if <code>out=webp</code> or <code>out=jpg</code>.</td></tr>
        </tbody>
      </table></div>
      <div class="note">
        <strong>Recommended usage from Postman or any client:</strong> put <code>out</code>, <code>size</code>, and <code>lossy</code> as URL query params, not as form fields.<br>
        <code>POST /api/v1/media/images/compress?out=webp&amp;size=1920</code><br>
        <code>POST /api/v1/media/images/compress?lossy=true</code>
      </div>
    </section>

    <section id="en-limits">
      <h2>Limits</h2>
      <ul>
        <li>Max <strong>10 files</strong> per request</li>
        <li>Max <strong>50 MB</strong> per file</li>
        <li>Max <strong>200 MB</strong> total batch</li>
        <li>Processing timeout: <strong>85 seconds</strong></li>
      </ul>
      <div class="note">Images are processed sequentially. If the timeout is reached mid-batch, already-processed images are returned with HTTP <code>206</code> and <code>X-Optimus-Status: partial</code>.</div>
    </section>

    <section id="en-response">
      <h2>Response &amp; Headers</h2>
      <h3>Body</h3>
      <ul>
        <li><strong>Single image:</strong> direct file response (<code>image/jpeg</code>, <code>image/png</code>, or <code>image/webp</code>)</li>
        <li><strong>Multiple images:</strong> ZIP archive (<code>application/zip</code>, filename: <code>compressed_images.zip</code>)</li>
      </ul>
      <h3>Custom response headers</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>Header</th><th>Values</th><th>Meaning</th></tr></thead>
        <tbody>
          <tr><td><code>X-Optimus-Status</code></td><td><code>complete</code> / <code>partial</code></td><td>Whether all images were processed</td></tr>
          <tr><td><code>X-Optimus-Processed</code></td><td>integer</td><td>Images successfully compressed</td></tr>
          <tr><td><code>X-Optimus-Total</code></td><td>integer</td><td>Total images received</td></tr>
          <tr><td><code>X-Optimus-Input-Size</code></td><td>bytes</td><td>Total size of all input images</td></tr>
          <tr><td><code>X-Optimus-Output-Size</code></td><td>bytes</td><td>Total size of all compressed results</td></tr>
          <tr><td><code>X-Optimus-Reduction-Pct</code></td><td>float</td><td>Size reduction percentage (e.g. <code>83.6</code>)</td></tr>
          <tr><td><code>Access-Control-Expose-Headers</code></td><td>list</td><td>Exposes X-Optimus-* to browser fetch()</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="en-status">
      <h2>HTTP Status Codes</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Code</th><th>Meaning</th></tr></thead>
        <tbody class="status-row">
          <tr><td class="s200">200</td><td>All images processed</td></tr>
          <tr><td class="s206">206</td><td>Partial &middot; timeout hit after &ge;1 image</td></tr>
          <tr><td class="s401">401</td><td>Missing or invalid <code>X-API-Key</code></td></tr>
          <tr><td class="s408">408</td><td>Timeout &middot; 0 images processed in 85 s</td></tr>
          <tr><td class="s422">422</td><td>Validation error (bad params, unsupported format, file too large&hellip;)</td></tr>
          <tr><td class="s503">503</td><td>Server busy &middot; image capacity or video queue full (<code>retry_after_seconds</code> in body)</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="en-examples">
      <h2>curl Examples</h2>
      <h3>Compress keeping original format</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.jpg" \\
  --output compressed.jpg</code></pre>
      <h3>Convert to WebP (recommended &middot; highest compression)</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp" \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.png" \\
  --output compressed.webp</code></pre>
      <h3>Lossy PNG: keep PNG format, ~80% reduction</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?lossy=true" \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.png" \\
  --output compressed.png</code></pre>
      <h3>Convert to WebP and resize to max 1920 px</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp&amp;size=1920" \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.png" \\
  --output compressed.webp</code></pre>
      <h3>Batch &middot; multiple images &rarr; ZIP</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp" \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo1.jpg" \\
  -F "files=@photo2.png" \\
  -F "files=@photo3.webp" \\
  --output result.zip</code></pre>
      <h3>Read response headers</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp" \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.jpg" \\
  -D - --output compressed.webp 2&gt;&amp;1 | grep -i "x-optimus"</code></pre>
    </section>

    <section id="en-video">
      <h2>Video Compression</h2>
      <p>Videos cannot be compressed in a single synchronous request (Cloudflare limit: 100 MB per request; FFmpeg compression can take minutes). The flow uses <strong>chunked upload</strong> + async processing with status polling.</p>

      <h3>Flow</h3>
      <ol>
        <li><strong>Init</strong>: start an upload session, receive an <code>upload_id</code></li>
        <li><strong>Chunks</strong>: send the video in pieces of &le;90 MB, <em>in order</em></li>
        <li><strong>Finalize</strong>: signal the server that all chunks were sent; receive a <code>job_id</code> with <code>status: queued</code></li>
        <li><strong>Poll</strong>: query <code>/status/{job_id}</code> every few seconds until <code>done</code> or <code>failed</code></li>
        <li><strong>Download</strong>: fetch the compressed video; the file is deleted from the server once the transfer completes</li>
      </ol>

      <h3>Limits</h3>
      <ul>
        <li>Max video size: <strong>500 MB</strong></li>
        <li>Max chunk size: <strong>90 MB</strong></li>
        <li>Accepted formats: <strong>mp4, mov, avi, mkv</strong></li>
        <li>Max queue: <strong>5 jobs</strong> &middot; if full, responds <code>503</code> with <code>retry_after_seconds: 60</code></li>
        <li>Compressed file kept for <strong>30 minutes</strong> after completion, or deleted immediately after a successful download</li>
      </ul>

      <h3>Endpoint parameters</h3>

      <h4>POST /upload/init (JSON body)</h4>
      <div class="table-wrap"><table>
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>filename</code></td><td>string</td><td>Yes</td><td>Original file name including extension. Allowed: <code>.mp4</code> <code>.mov</code> <code>.avi</code> <code>.mkv</code></td></tr>
          <tr><td><code>total_size</code></td><td>integer</td><td>Yes</td><td>Total video size in <strong>bytes</strong>. Max 500 MB (524,288,000 bytes). Must be &gt; 0.</td></tr>
          <tr><td><code>total_chunks</code></td><td>integer</td><td>Yes</td><td>Number of chunks the video will be split into. Between 1 and 128.</td></tr>
        </tbody>
      </table></div>
      <p>Response: <code>{ upload_id, chunk_size_recommended }</code></p>

      <h4>POST /upload/chunk (multipart/form-data)</h4>
      <div class="note">Do <strong>not</strong> set <code>Content-Type: application/json</code> for this endpoint — the browser/fetch sets it automatically as <code>multipart/form-data</code> when you pass a <code>FormData</code> object.</div>
      <div class="table-wrap"><table>
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>upload_id</code></td><td>string (form)</td><td>Yes</td><td>The UUID returned by <code>/init</code></td></tr>
          <tr><td><code>chunk_index</code></td><td>integer (form)</td><td>Yes</td><td>0-based index of this chunk. Must be sent in order: 0, 1, 2&hellip;</td></tr>
          <tr><td><code>chunk</code></td><td>file (form)</td><td>Yes</td><td>Binary slice of the video. Max 90 MB per chunk.</td></tr>
        </tbody>
      </table></div>
      <p>Response: <code>{ received, total }</code></p>

      <h4>POST /upload/finalize (JSON body)</h4>
      <div class="table-wrap"><table>
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>upload_id</code></td><td>string</td><td>Yes</td><td>The same UUID used during chunk upload</td></tr>
        </tbody>
      </table></div>
      <p>Response: <code>{ job_id, status: "queued" }</code></p>

      <h4>GET /status/{job_id} (no body)</h4>
      <p>Pass <code>X-API-Key</code> header only. Returns the full job state object (see <em>Status response</em> below).</p>

      <h4>GET /download/{job_id} (no body)</h4>
      <p>Pass <code>X-API-Key</code> header only. Available only when <code>status === "done"</code>. Returns the compressed <code>video/mp4</code> file. The file is deleted from the server after transfer, do <strong>not</strong> use <code>window.location.href</code> (cannot send headers). Use <code>fetch</code> + blob instead (see JS example).</p>

      <h3>Job states</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>Status</th><th>Meaning</th></tr></thead>
        <tbody>
          <tr><td><code>uploading</code></td><td>Receiving chunks</td></tr>
          <tr><td><code>queued</code></td><td>All chunks received &middot; waiting for FFmpeg slot</td></tr>
          <tr><td><code>processing</code></td><td>FFmpeg compressing</td></tr>
          <tr><td><code>done</code></td><td>Ready to download</td></tr>
          <tr><td><code>failed</code></td><td>FFmpeg error or processing timeout</td></tr>
          <tr><td><code>expired</code></td><td>Upload abandoned (no chunk activity for 15 min)</td></tr>
        </tbody>
      </table></div>

      <h3>Status response</h3>
      <p>Each call to <code>/status/{job_id}</code> returns:</p>
      <pre><code>{
  "job_id":        "550e8400-...",
  "status":        "processing",   // uploading | queued | processing | done | failed | expired
  "progress_pct":  42,             // 0–99 while processing; 100 when done
  "input_size":    0,              // bytes — available when done
  "output_size":   0,              // bytes — available when done
  "reduction_pct": 0.0,            // e.g. 67.3 — available when done
  "error_msg":     null,           // string if failed
  "file_deleted":  false           // true after a successful download
}</code></pre>
      <div class="note">
        <strong>Building a progress bar:</strong> use <code>progress_pct</code> (integer 0–100) directly as the bar width percentage. Show an indeterminate spinner when <code>status</code> is <code>queued</code>. During <code>processing</code>, <code>progress_pct</code> rises from 0 to 99. It reaches 100 only when <code>status === "done"</code>.
      </div>

      <h3>JavaScript example</h3>
      <pre><code>const API   = 'https://optimus.azanolabs.com';
const KEY   = 'your-key';
const CHUNK = 80 * 1024 * 1024; // 80 MB per chunk

async function compressVideo(file) {
  const totalChunks = Math.ceil(file.size / CHUNK);

  // 1. Init
  const { upload_id } = await fetch(`${API}/api/v1/media/videos/upload/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({
      filename: file.name,
      total_size: file.size,
      total_chunks: totalChunks
    })
  }).then(r =&gt; r.json());

  // 2. Chunks (sequential, order matters)
  for (let i = 0; i &lt; totalChunks; i++) {
    const form = new FormData();
    form.append('upload_id', upload_id);
    form.append('chunk_index', String(i));
    form.append('chunk', file.slice(i * CHUNK, (i + 1) * CHUNK));
    await fetch(`${API}/api/v1/media/videos/upload/chunk`, {
      method: 'POST', headers: { 'X-API-Key': KEY }, body: form
    });
  }

  // 3. Finalize: responds { job_id, status: 'queued' }
  const { job_id } = await fetch(`${API}/api/v1/media/videos/upload/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({ upload_id })
  }).then(r =&gt; r.json());

  // 4. Poll every 3 s — use job.progress_pct (0–100) to drive a progress bar
  let job;
  do {
    await new Promise(r =&gt; setTimeout(r, 3000));
    job = await fetch(`${API}/api/v1/media/videos/status/${job_id}`,
      { headers: { 'X-API-Key': KEY } }).then(r =&gt; r.json());
    // e.g. document.getElementById('bar').value = job.progress_pct;
  } while (job.status === 'queued' || job.status === 'processing');

  // 5. Download — fetch with header, trigger browser download via blob
  // (window.location.href cannot send X-API-Key — would return 401)
  if (job.status === 'done') {
    const res  = await fetch(`${API}/api/v1/media/videos/download/${job_id}`,
      { headers: { 'X-API-Key': KEY } });
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'compressed_video.mp4'; a.click();
    URL.revokeObjectURL(url);
  } else {
    console.error('Compression failed:', job.error_msg);
  }
}</code></pre>
    </section>

  </div><!-- #lang-en -->

  <!-- ==================== ESPAÑOL ==================== -->
  <div id="lang-es" class="lang-content">

    <div class="toc">
      <h2>Contenido</h2>
      <ol>
        <li><a href="#es-auth">Autenticaci&oacute;n</a></li>
        <li><a href="#es-endpoints">Endpoints</a></li>
        <li><a href="#es-params">Par&aacute;metros</a></li>
        <li><a href="#es-limits">L&iacute;mites</a></li>
        <li><a href="#es-response">Respuesta y Headers</a></li>
        <li><a href="#es-status">C&oacute;digos de estado HTTP</a></li>
        <li><a href="#es-examples">Ejemplos con curl</a></li>
        <li><a href="#es-video">Compresi&oacute;n de video</a></li>
      </ol>
    </div>

    <section id="es-auth">
      <h2>Autenticaci&oacute;n</h2>
      <p>Los endpoints bajo <code>/api/v1/</code> soportan dos m&eacute;todos de autenticaci&oacute;n:</p>
      <h3>API Key maestra (servidor a servidor)</h3>
      <p>Usada por tu backend (ej. una funci&oacute;n serverless de Vercel). <strong>Nunca expongas esta clave en el navegador.</strong></p>
      <pre><code>X-API-Key: tu-clave-secreta</code></pre>
      <h3>Token de sesi&oacute;n (llamadas directas desde el navegador)</h3>
      <p>Token de corta duraci&oacute;n (TTL de 2&nbsp;h) obtenido del lado del servidor via <code>POST /api/v1/auth/session-token</code> y enviado al navegador. Permite que el navegador llame al VPS directamente sin exponer la clave maestra.</p>
      <pre><code>X-Session-Token: &lt;token&gt;</code></pre>
      <h4>Ciclo de vida del token</h4>
      <ul>
        <li>V&aacute;lido por <strong>2 horas</strong> desde su emisi&oacute;n</li>
        <li>Renovar proactivamente ~12 min antes de que expire para evitar fallos a mitad de subida</li>
        <li>Si el token vence durante una subida, cancela el job (<code>DELETE /upload/{upload_id}</code>) y reintenta con un token nuevo</li>
        <li>Los tokens viven en memoria del servidor, reiniciar el VPS invalida todos los tokens activos</li>
      </ul>
      <p>Las peticiones sin clave o token v&aacute;lido devuelven <code>401 Unauthorized</code>. Los endpoints <code>GET /guide</code> y <code>GET /guide-ai</code> son p&uacute;blicos &middot; no requieren autenticaci&oacute;n.</p>
    </section>

    <section id="es-endpoints">
      <h2>Endpoints</h2>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/guide</span>
          <span class="auth-badge">p&uacute;blico</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Esta p&aacute;gina. Referencia de la API en HTML.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/guide-ai</span>
          <span class="auth-badge">p&uacute;blico</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Referencia JSON optimizada para agentes de IA (LLMs, LangChain, MCP, etc.). Mismo contenido que esta gu&iacute;a pero estructurado para consumo program&aacute;tico, sin necesidad de parsear HTML.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/auth/session-token</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Intercambia la API key maestra por un token de sesi&oacute;n de corta duraci&oacute;n (2&nbsp;h TTL). Llama esto desde el servidor y env&iacute;a el token al navegador. El navegador entonces se autentica con <code>X-Session-Token</code> para llamar al VPS directamente. Body: ninguno. Respuesta: <code>{ token, expires_in }</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/images/compress</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Comprime una o varias im&aacute;genes. Acepta <code>multipart/form-data</code>. Devuelve la imagen comprimida o un ZIP.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/init</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Inicia una sesi&oacute;n de subida. Body: <code>{filename, total_size, total_chunks}</code>. Devuelve <code>upload_id</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/chunk</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Sube un fragmento del video (m&aacute;x. 90 MB). Form-data: <code>upload_id</code>, <code>chunk_index</code> (desde 0), <code>chunk</code> (archivo). Repetir en orden.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/upload/finalize</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Notifica que se enviaron todos los chunks. Body: <code>{upload_id}</code>. Devuelve <code>job_id</code> con <code>status: queued</code>. Responde <code>503</code> si la cola est&aacute; llena.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/api/v1/media/videos/status/{job_id}</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Consulta el estado de la compresi&oacute;n. Devuelve <code>status</code>, <code>progress_pct</code>, <code>input_size</code>, <code>output_size</code>, <code>reduction_pct</code>, <code>error_msg</code>.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method get">GET</span>
          <span class="path">/api/v1/media/videos/download/{job_id}</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Descarga el video comprimido. Solo disponible cuando <code>status: done</code>. El archivo se elimina del servidor al terminar la transferencia.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method delete">DELETE</span>
          <span class="path">/api/v1/media/videos/upload/{upload_id}</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Cancela y limpia un job en cualquier estado (subiendo, en cola, comprimiendo, listo). Mata FFmpeg si est&aacute; corriendo y elimina todos los archivos temporales. Devuelve <code>{cancelled: true, job_id}</code>. Devuelve <code>404</code> si ya no existe.</p>
      </div>
    </section>

    <section id="es-params">
      <h2>Par&aacute;metros &middot; POST /api/v1/media/images/compress</h2>
      <p>El campo <code>files</code> debe enviarse como <code>multipart/form-data</code>. Los par&aacute;metros opcionales <code>out</code>, <code>size</code> y <code>lossy</code> se aceptan tanto como campos de formulario <strong>como query params en la URL</strong>. Se recomienda usar query params para evitar problemas de parseo multipart en algunos clientes (ej. Postman).</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Campo</th><th>Tipo</th><th>Requerido</th><th>Default</th><th>Descripci&oacute;n</th></tr></thead>
        <tbody>
          <tr><td><code>files</code></td><td>archivo(s)</td><td>S&iacute;</td><td>&middot;</td><td>1&ndash;10 im&aacute;genes. Permitidos: <code>.jpg</code> <code>.jpeg</code> <code>.png</code> <code>.webp</code></td></tr>
          <tr><td><code>out</code></td><td>string</td><td>No</td><td>conservar</td><td>Formato de salida: <code>jpg</code>, <code>webp</code> o <code>png</code>. Convierte todas las im&aacute;genes al formato indicado.</td></tr>
          <tr><td><code>size</code></td><td>entero</td><td>No</td><td>sin resize</td><td>Dimensi&oacute;n m&aacute;xima en el lado m&aacute;s largo (1&ndash;8000). Proporci&oacute;n conservada. Nunca amplía.</td></tr>
          <tr><td><code>lossy</code></td><td>boolean</td><td>No</td><td>false</td><td>Compresi&oacute;n PNG lossy mediante cuantizaci&oacute;n de color (estilo pngquant, 256 colores). Solo aplica cuando el formato de salida es PNG. Logra ~80% de reducci&oacute;n. Ignorado si <code>out=webp</code> o <code>out=jpg</code>.</td></tr>
        </tbody>
      </table></div>
      <div class="note">
        <strong>Uso recomendado desde Postman o cualquier cliente:</strong> poner <code>out</code>, <code>size</code> y <code>lossy</code> como query params en la URL, no como campos de formulario.<br>
        <code>POST /api/v1/media/images/compress?out=webp&amp;size=1920</code><br>
        <code>POST /api/v1/media/images/compress?lossy=true</code>
      </div>
    </section>

    <section id="es-limits">
      <h2>L&iacute;mites</h2>
      <ul>
        <li>M&aacute;ximo <strong>10 archivos</strong> por petici&oacute;n</li>
        <li>M&aacute;ximo <strong>50 MB</strong> por archivo</li>
        <li>M&aacute;ximo <strong>200 MB</strong> total del lote</li>
        <li>Timeout de procesamiento: <strong>85 segundos</strong></li>
      </ul>
      <div class="note">Las im&aacute;genes se procesan secuencialmente. Si se alcanza el timeout, las ya procesadas se devuelven con HTTP <code>206</code> y <code>X-Optimus-Status: partial</code>.</div>
    </section>

    <section id="es-response">
      <h2>Respuesta y Headers</h2>
      <h3>Cuerpo</h3>
      <ul>
        <li><strong>Una imagen:</strong> archivo directo (<code>image/jpeg</code>, <code>image/png</code> o <code>image/webp</code>)</li>
        <li><strong>Varias im&aacute;genes:</strong> ZIP (<code>application/zip</code>, nombre: <code>compressed_images.zip</code>)</li>
      </ul>
      <h3>Headers de respuesta personalizados</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>Header</th><th>Valores</th><th>Significado</th></tr></thead>
        <tbody>
          <tr><td><code>X-Optimus-Status</code></td><td><code>complete</code> / <code>partial</code></td><td>Si se procesaron todas las im&aacute;genes</td></tr>
          <tr><td><code>X-Optimus-Processed</code></td><td>entero</td><td>Im&aacute;genes comprimidas exitosamente</td></tr>
          <tr><td><code>X-Optimus-Total</code></td><td>entero</td><td>Total de im&aacute;genes recibidas</td></tr>
          <tr><td><code>X-Optimus-Input-Size</code></td><td>bytes</td><td>Tama&ntilde;o total de las im&aacute;genes de entrada</td></tr>
          <tr><td><code>X-Optimus-Output-Size</code></td><td>bytes</td><td>Tama&ntilde;o total del resultado comprimido</td></tr>
          <tr><td><code>X-Optimus-Reduction-Pct</code></td><td>float</td><td>Porcentaje de reducci&oacute;n (ej. <code>83.6</code>)</td></tr>
          <tr><td><code>Access-Control-Expose-Headers</code></td><td>lista</td><td>Expone los X-Optimus-* al fetch() del navegador</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="es-status">
      <h2>C&oacute;digos de estado HTTP</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>C&oacute;digo</th><th>Significado</th></tr></thead>
        <tbody class="status-row">
          <tr><td class="s200">200</td><td>Todas las im&aacute;genes procesadas</td></tr>
          <tr><td class="s206">206</td><td>Parcial &middot; timeout tras &ge;1 imagen</td></tr>
          <tr><td class="s401">401</td><td><code>X-API-Key</code> ausente o inv&aacute;lido</td></tr>
          <tr><td class="s408">408</td><td>Timeout &middot; 0 im&aacute;genes procesadas en 85 s</td></tr>
          <tr><td class="s422">422</td><td>Error de validaci&oacute;n (params inv&aacute;lidos, formato no soportado, archivo muy grande&hellip;)</td></tr>
          <tr><td class="s503">503</td><td>Servidor ocupado &middot; capacidad de im&aacute;genes o cola de video llena (<code>retry_after_seconds</code> en el body)</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="es-examples">
      <h2>Ejemplos con curl</h2>
      <h3>Comprimir conservando el formato original</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.jpg" \\
  --output comprimido.jpg</code></pre>
      <h3>Convertir a WebP (recomendado &middot; m&aacute;xima compresi&oacute;n)</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp" \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.png" \\
  --output comprimido.webp</code></pre>
      <h3>PNG lossy: conservar formato PNG, ~80% de reducci&oacute;n</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?lossy=true" \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.png" \\
  --output comprimido.png</code></pre>
      <h3>Convertir a WebP y redimensionar a m&aacute;x. 1920 px</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp&amp;size=1920" \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.png" \\
  --output comprimido.webp</code></pre>
      <h3>Lote &middot; varias im&aacute;genes &rarr; ZIP</h3>
      <pre><code>curl -X POST "https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp" \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto1.jpg" \\
  -F "files=@foto2.png" \\
  -F "files=@foto3.webp" \\
  --output resultado.zip</code></pre>
    </section>

    <section id="es-video">
      <h2>Compresi&oacute;n de video</h2>
      <p>Los videos no pueden comprimirse en una sola petici&oacute;n s&iacute;ncrona (l&iacute;mite de Cloudflare: 100 MB por petici&oacute;n; la compresi&oacute;n con FFmpeg puede tardar minutos). El flujo usa <strong>subida por fragmentos</strong> + procesamiento async con polling de estado.</p>

      <h3>Flujo</h3>
      <ol>
        <li><strong>Init</strong>: inicia una sesi&oacute;n de subida, recibe un <code>upload_id</code></li>
        <li><strong>Chunks</strong>: env&iacute;a el video en partes de &le;90 MB, <em>en orden</em></li>
        <li><strong>Finalize</strong>: notifica al servidor que se enviaron todos los chunks; recibe un <code>job_id</code> con <code>status: queued</code></li>
        <li><strong>Poll</strong>: consulta <code>/status/{job_id}</code> cada pocos segundos hasta <code>done</code> o <code>failed</code></li>
        <li><strong>Descarga</strong>: descarga el video comprimido; el archivo se elimina del servidor al terminar la transferencia</li>
      </ol>

      <h3>L&iacute;mites</h3>
      <ul>
        <li>Tama&ntilde;o m&aacute;ximo del video: <strong>500 MB</strong></li>
        <li>Tama&ntilde;o m&aacute;ximo por chunk: <strong>90 MB</strong></li>
        <li>Formatos aceptados: <strong>mp4, mov, avi, mkv</strong></li>
        <li>Cola m&aacute;x.: <strong>5 jobs</strong> &middot; si est&aacute; llena, responde <code>503</code> con <code>retry_after_seconds: 60</code></li>
        <li>El archivo comprimido se guarda <strong>30 minutos</strong> tras la compresi&oacute;n, o se elimina inmediatamente despu&eacute;s de una descarga exitosa</li>
      </ul>

      <h3>Par&aacute;metros de endpoints</h3>

      <h4>POST /upload/init (JSON body)</h4>
      <div class="table-wrap"><table>
        <thead><tr><th>Campo</th><th>Tipo</th><th>Requerido</th><th>Descripci&oacute;n</th></tr></thead>
        <tbody>
          <tr><td><code>filename</code></td><td>string</td><td>S&iacute;</td><td>Nombre original del archivo con extensi&oacute;n. Permitidos: <code>.mp4</code> <code>.mov</code> <code>.avi</code> <code>.mkv</code></td></tr>
          <tr><td><code>total_size</code></td><td>entero</td><td>S&iacute;</td><td>Tama&ntilde;o total del video en <strong>bytes</strong>. M&aacute;x. 500 MB (524.288.000 bytes). Debe ser &gt; 0.</td></tr>
          <tr><td><code>total_chunks</code></td><td>entero</td><td>S&iacute;</td><td>N&uacute;mero de chunks en que se divide el video. Entre 1 y 128.</td></tr>
        </tbody>
      </table></div>
      <p>Respuesta: <code>{ upload_id, chunk_size_recommended }</code></p>

      <h4>POST /upload/chunk (multipart/form-data)</h4>
      <div class="note">No fijes <code>Content-Type: application/json</code> en este endpoint, el navegador/fetch lo establece autom&aacute;ticamente como <code>multipart/form-data</code> al pasar un objeto <code>FormData</code>.</div>
      <div class="table-wrap"><table>
        <thead><tr><th>Campo</th><th>Tipo</th><th>Requerido</th><th>Descripci&oacute;n</th></tr></thead>
        <tbody>
          <tr><td><code>upload_id</code></td><td>string (form)</td><td>S&iacute;</td><td>El UUID retornado por <code>/init</code></td></tr>
          <tr><td><code>chunk_index</code></td><td>entero (form)</td><td>S&iacute;</td><td>&Iacute;ndice 0-based de este chunk. Debe enviarse en orden: 0, 1, 2&hellip;</td></tr>
          <tr><td><code>chunk</code></td><td>archivo (form)</td><td>S&iacute;</td><td>Fragmento binario del video. M&aacute;x. 90 MB por chunk.</td></tr>
        </tbody>
      </table></div>
      <p>Respuesta: <code>{ received, total }</code></p>

      <h4>POST /upload/finalize (JSON body)</h4>
      <div class="table-wrap"><table>
        <thead><tr><th>Campo</th><th>Tipo</th><th>Requerido</th><th>Descripci&oacute;n</th></tr></thead>
        <tbody>
          <tr><td><code>upload_id</code></td><td>string</td><td>S&iacute;</td><td>El mismo UUID utilizado durante la subida de chunks</td></tr>
        </tbody>
      </table></div>
      <p>Respuesta: <code>{ job_id, status: "queued" }</code></p>

      <h4>GET /status/{job_id} (sin body)</h4>
      <p>Solo el header <code>X-API-Key</code>. Retorna el objeto completo del job (ver <em>Respuesta del endpoint de estado</em> m&aacute;s abajo).</p>

      <h4>GET /download/{job_id} (sin body)</h4>
      <p>Solo el header <code>X-API-Key</code>. Disponible solo cuando <code>status === "done"</code>. Retorna el archivo comprimido <code>video/mp4</code>. El archivo se elimina tras la transferencia, <strong>no</strong> uses <code>window.location.href</code> (no puede enviar headers). Usa <code>fetch</code> + blob (ver ejemplo JS).</p>

      <h3>Estados del job</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>Estado</th><th>Significado</th></tr></thead>
        <tbody>
          <tr><td><code>uploading</code></td><td>Recibiendo chunks</td></tr>
          <tr><td><code>queued</code></td><td>Todos los chunks recibidos &middot; esperando slot de FFmpeg</td></tr>
          <tr><td><code>processing</code></td><td>FFmpeg comprimiendo</td></tr>
          <tr><td><code>done</code></td><td>Listo para descargar</td></tr>
          <tr><td><code>failed</code></td><td>Error de FFmpeg o timeout de procesamiento</td></tr>
          <tr><td><code>expired</code></td><td>Upload abandonado (sin actividad en 15 min)</td></tr>
        </tbody>
      </table></div>

      <h3>Respuesta del endpoint de estado</h3>
      <p>Cada llamada a <code>/status/{job_id}</code> retorna:</p>
      <pre><code>{
  "job_id":        "550e8400-...",
  "status":        "processing",   // uploading | queued | processing | done | failed | expired
  "progress_pct":  42,             // 0–99 mientras procesa; 100 cuando done
  "input_size":    0,              // bytes — disponible cuando done
  "output_size":   0,              // bytes — disponible cuando done
  "reduction_pct": 0.0,            // ej. 67.3 — disponible cuando done
  "error_msg":     null,           // string si fall&oacute;
  "file_deleted":  false           // true tras una descarga exitosa
}</code></pre>
      <div class="note">
        <strong>Barra de progreso:</strong> usa <code>progress_pct</code> (entero 0–100) directamente como el porcentaje de ancho de la barra. Muestra un spinner indeterminado cuando <code>status</code> es <code>queued</code>. Durante <code>processing</code>, <code>progress_pct</code> sube de 0 a 99. Llega a 100 solo cuando <code>status === "done"</code>.
      </div>

      <h3>Ejemplo JavaScript</h3>
      <pre><code>const API   = 'https://optimus.azanolabs.com';
const KEY   = 'tu-clave';
const CHUNK = 80 * 1024 * 1024; // 80 MB por chunk

async function comprimirVideo(file) {
  const totalChunks = Math.ceil(file.size / CHUNK);

  // 1. Init
  const { upload_id } = await fetch(`${API}/api/v1/media/videos/upload/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({
      filename: file.name,
      total_size: file.size,
      total_chunks: totalChunks
    })
  }).then(r =&gt; r.json());

  // 2. Chunks (enviar en orden, el orden importa)
  for (let i = 0; i &lt; totalChunks; i++) {
    const form = new FormData();
    form.append('upload_id', upload_id);
    form.append('chunk_index', String(i));
    form.append('chunk', file.slice(i * CHUNK, (i + 1) * CHUNK));
    await fetch(`${API}/api/v1/media/videos/upload/chunk`, {
      method: 'POST', headers: { 'X-API-Key': KEY }, body: form
    });
  }

  // 3. Finalize: responde { job_id, status: 'queued' }
  const { job_id } = await fetch(`${API}/api/v1/media/videos/upload/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({ upload_id })
  }).then(r =&gt; r.json());

  // 4. Polling cada 3 s — usa job.progress_pct (0–100) para actualizar la barra
  let job;
  do {
    await new Promise(r =&gt; setTimeout(r, 3000));
    job = await fetch(`${API}/api/v1/media/videos/status/${job_id}`,
      { headers: { 'X-API-Key': KEY } }).then(r =&gt; r.json());
    // ej. document.getElementById('barra').value = job.progress_pct;
  } while (job.status === 'queued' || job.status === 'processing');

  // 5. Descarga — fetch con header, disparar descarga en browser via blob
  // (window.location.href no puede enviar X-API-Key — devolvería 401)
  if (job.status === 'done') {
    const res  = await fetch(`${API}/api/v1/media/videos/download/${job_id}`,
      { headers: { 'X-API-Key': KEY } });
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'compressed_video.mp4'; a.click();
    URL.revokeObjectURL(url);
  } else {
    console.error('Error en la compresión:', job.error_msg);
  }
}</code></pre>
    </section>

  </div><!-- #lang-es -->

</div><!-- .container -->

<script>
  function switchLang(lang, card) {
    document.querySelectorAll('.lang-card').forEach(function(c) { c.classList.remove('active'); });
    card.classList.add('active');
    document.querySelectorAll('.lang-content').forEach(function(el) { el.classList.remove('visible'); });
    document.getElementById('lang-' + lang).classList.add('visible');
    document.documentElement.lang = lang;
  }
</script>

</body>
</html>"""


def get_guide() -> HTMLResponse:
    return HTMLResponse(content=_GUIDE_HTML)
