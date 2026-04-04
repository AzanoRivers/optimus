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
    .get  { background: #0e4429; color: #3fb950; }
    .post { background: #1f2d5a; color: #79c0ff; }
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

    .status-row td:first-child { font-family: monospace; font-weight: 700; }
    .s200 { color: #3fb950; }
    .s206 { color: #79c0ff; }
    .s401 { color: #f0883e; }
    .s408 { color: #f0883e; }
    .s422 { color: #d2a8ff; }
    .s501 { color: #8b949e; }

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
      </ol>
    </div>

    <section id="en-auth">
      <h2>Authentication</h2>
      <p>All endpoints under <code>/api/v1/</code> require an API key in the request header:</p>
      <pre><code>X-API-Key: your-secret-key</code></pre>
      <p>Requests without a valid key return <code>401 Unauthorized</code>.</p>
      <p>The <code>GET /guide</code> endpoint is public &middot; no key required.</p>
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
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/images/compress</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Compress one or more images. Accepts <code>multipart/form-data</code>. Returns a single compressed image or a ZIP archive.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/compress</span>
          <span class="auth-badge required">X-API-Key required</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem"><em>Not implemented yet.</em> Returns <code>501</code>.</p>
      </div>
    </section>

    <section id="en-params">
      <h2>Parameters &middot; POST /api/v1/media/images/compress</h2>
      <p>Send as <code>multipart/form-data</code>. All fields must be form fields, not query params.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>files</code></td><td>file(s)</td><td>Yes</td><td>&middot;</td><td>1&ndash;10 images. Allowed: <code>.jpg</code> <code>.jpeg</code> <code>.png</code> <code>.webp</code></td></tr>
          <tr><td><code>out</code></td><td>string</td><td>No</td><td>keep original</td><td>Output format: <code>jpg</code>, <code>webp</code>, or <code>png</code></td></tr>
          <tr><td><code>size</code></td><td>integer</td><td>No</td><td>no resize</td><td>Max pixel on longest side (1&ndash;8000). Aspect ratio preserved.</td></tr>
        </tbody>
      </table></div>
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
          <tr><td class="s501">501</td><td>Video compression not implemented</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="en-examples">
      <h2>curl Examples</h2>
      <h3>Compress a single image</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.jpg" \\
  --output compressed.jpg</code></pre>
      <h3>Convert to WebP and resize to max 1200 px</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.png" \\
  -F "out=webp" \\
  -F "size=1200" \\
  --output compressed.webp</code></pre>
      <h3>Batch &middot; multiple images &rarr; ZIP</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo1.jpg" \\
  -F "files=@photo2.png" \\
  -F "files=@photo3.webp" \\
  -F "out=webp" \\
  --output result.zip</code></pre>
      <h3>Read response headers</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: your-key" \\
  -F "files=@photo.jpg" \\
  -D - --output compressed.jpg 2&gt;&amp;1 | grep -i "x-optimus"</code></pre>
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
      </ol>
    </div>

    <section id="es-auth">
      <h2>Autenticaci&oacute;n</h2>
      <p>Todos los endpoints bajo <code>/api/v1/</code> requieren una API key en el header de la petici&oacute;n:</p>
      <pre><code>X-API-Key: tu-clave-secreta</code></pre>
      <p>Las peticiones sin clave v&aacute;lida devuelven <code>401 Unauthorized</code>.</p>
      <p>El endpoint <code>GET /guide</code> es p&uacute;blico &middot; no requiere clave.</p>
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
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/images/compress</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem">Comprime una o varias im&aacute;genes. Acepta <code>multipart/form-data</code>. Devuelve la imagen comprimida o un ZIP.</p>
      </div>
      <div class="endpoint">
        <div class="endpoint-header">
          <span class="method post">POST</span>
          <span class="path">/api/v1/media/videos/compress</span>
          <span class="auth-badge required">X-API-Key requerido</span>
        </div>
        <p style="margin-top:0.5rem;font-size:0.85rem"><em>No implementado todav&iacute;a.</em> Devuelve <code>501</code>.</p>
      </div>
    </section>

    <section id="es-params">
      <h2>Par&aacute;metros &middot; POST /api/v1/media/images/compress</h2>
      <p>Enviar como <code>multipart/form-data</code>. Todos los campos deben ser campos de formulario, no query params.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Campo</th><th>Tipo</th><th>Requerido</th><th>Default</th><th>Descripci&oacute;n</th></tr></thead>
        <tbody>
          <tr><td><code>files</code></td><td>archivo(s)</td><td>S&iacute;</td><td>&middot;</td><td>1&ndash;10 im&aacute;genes. Permitidos: <code>.jpg</code> <code>.jpeg</code> <code>.png</code> <code>.webp</code></td></tr>
          <tr><td><code>out</code></td><td>string</td><td>No</td><td>conservar</td><td>Formato de salida: <code>jpg</code>, <code>webp</code>, o <code>png</code></td></tr>
          <tr><td><code>size</code></td><td>entero</td><td>No</td><td>sin resize</td><td>Dimensi&oacute;n m&aacute;xima (lado m&aacute;s largo, 1&ndash;8000). Proporci&oacute;n conservada.</td></tr>
        </tbody>
      </table></div>
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
          <tr><td class="s501">501</td><td>Compresi&oacute;n de video no implementada</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="es-examples">
      <h2>Ejemplos con curl</h2>
      <h3>Comprimir una imagen (conservar formato)</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.jpg" \\
  --output comprimido.jpg</code></pre>
      <h3>Convertir a WebP y redimensionar a m&aacute;x. 1200 px</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto.png" \\
  -F "out=webp" \\
  -F "size=1200" \\
  --output comprimido.webp</code></pre>
      <h3>Lote &middot; varias im&aacute;genes &rarr; ZIP</h3>
      <pre><code>curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress \\
  -H "X-API-Key: tu-clave" \\
  -F "files=@foto1.jpg" \\
  -F "files=@foto2.png" \\
  -F "files=@foto3.webp" \\
  -F "out=webp" \\
  --output resultado.zip</code></pre>
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
