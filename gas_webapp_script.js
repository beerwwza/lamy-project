/**
 * LAMY Document Upload — Google Apps Script Web App
 *
 * วิธี deploy:
 *   1. เปิด Google Apps Script (script.google.com)
 *   2. วางโค้ดทั้งหมดนี้แทนที่โค้ดเดิม
 *   3. Deploy → New Deployment → Web App
 *      - Execute as: Me
 *      - Who has access: Anyone
 *   4. Copy URL → ใส่ใน .env เป็น GAS_WEBAPP_URL=<url>
 *
 * รองรับ 3 mode:
 *   action: 'upload'  — ไฟล์ ≤ 35 MB (base64 JSON เดิม)
 *   action: 'init'    — เริ่ม resumable session สำหรับไฟล์ > 35 MB
 *   action: 'chunk'   — ส่ง chunk ทีละก้อน (20 MB raw / ~26 MB base64)
 */

// ───────────────────────────────────────────────────────────────────────────
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ error: 'No POST body received' });
    }
    var data   = JSON.parse(e.postData.contents);
    var action = data.action || 'upload';

    if (action === 'upload') return handleSingleUpload(data);
    if (action === 'init')   return handleInit(data);
    if (action === 'chunk')  return handleChunk(data);

    return jsonResponse({ error: 'Unknown action: ' + action });
  } catch (err) {
    return jsonResponse({ error: 'doPost: ' + err.toString() });
  }
}

function doGet(e) {
  return jsonResponse({ status: 'LAMY GAS Web App is running' });
}

// ── Mode 1: Single upload (ไฟล์ ≤ 35 MB) ───────────────────────────────────
function handleSingleUpload(data) {
  try {
    var bytes  = Utilities.base64Decode(data.fileData);
    var blob   = Utilities.newBlob(bytes, data.mimeType, data.filename);
    var folder = getOrCreateFolder(data.folderPath);
    var file   = folder.createFile(blob);
    return jsonResponse({ fileId: file.getId() });
  } catch (err) {
    return jsonResponse({ error: err.message });
  }
}

// ── Mode 2: Init resumable session (ไฟล์ > 35 MB) ──────────────────────────
function handleInit(data) {
  try {
    var folderId    = getOrCreateFolder(data.folderPath).getId();
    var accessToken = ScriptApp.getOAuthToken();

    // สร้าง Drive resumable upload session
    var response = UrlFetchApp.fetch(
      'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
      {
        method: 'POST',
        headers: {
          'Authorization':           'Bearer ' + accessToken,
          'Content-Type':            'application/json; charset=UTF-8',
          'X-Upload-Content-Type':   data.mimeType,
          'X-Upload-Content-Length': String(data.fileSize)
        },
        payload: JSON.stringify({
          name:    data.filename,
          parents: [folderId]
        }),
        muteHttpExceptions: true
      }
    );

    var code      = response.getResponseCode();
    var uploadUrl = response.getHeaders()['location'] ||
                    response.getHeaders()['Location'];

    if (!uploadUrl) {
      return jsonResponse({
        error:  'ไม่ได้รับ upload URL จาก Drive API',
        code:   code,
        detail: response.getContentText()
      });
    }

    // เก็บ URL ไว้ใน Script Properties โดยใช้ uploadId เป็น key
    PropertiesService.getScriptProperties()
      .setProperty('upload_' + data.uploadId, uploadUrl);

    return jsonResponse({ status: 'ok', uploadId: data.uploadId });

  } catch (err) {
    return jsonResponse({ error: err.message });
  }
}

// ── Mode 3: Upload chunk ─────────────────────────────────────────────────────
function handleChunk(data) {
  try {
    var uploadUrl = PropertiesService.getScriptProperties()
      .getProperty('upload_' + data.uploadId);

    if (!uploadUrl) {
      return jsonResponse({ error: 'ไม่พบ upload session: ' + data.uploadId });
    }

    var chunkBytes  = Utilities.base64Decode(data.chunkData);
    var chunkStart  = data.chunkStart;
    var chunkEnd    = chunkStart + chunkBytes.length - 1;
    var fileSize    = data.fileSize;
    var isLast      = data.isLast;

    // Content-Range: bytes start-end/total  (last chunk) | bytes start-end/* (middle)
    var contentRange = isLast
      ? 'bytes ' + chunkStart + '-' + chunkEnd + '/' + fileSize
      : 'bytes ' + chunkStart + '-' + chunkEnd + '/*';

    var response = UrlFetchApp.fetch(uploadUrl, {
      method: 'PUT',
      headers: {
        'Content-Range': contentRange,
        'Content-Type':  data.mimeType
      },
      payload:           chunkBytes,
      muteHttpExceptions: true
    });

    var code = response.getResponseCode();

    // 200/201 = อัปโหลดเสร็จสมบูรณ์
    if (code === 200 || code === 201) {
      var result = JSON.parse(response.getContentText());
      PropertiesService.getScriptProperties()
        .deleteProperty('upload_' + data.uploadId);
      return jsonResponse({ status: 'done', fileId: result.id });
    }

    // 308 = Drive ยืนยันรับ chunk แล้ว รอ chunk ถัดไป
    if (code === 308) {
      return jsonResponse({ status: 'ok', chunkStart: chunkStart });
    }

    return jsonResponse({
      error:  'Drive API ตอบ HTTP ' + code,
      detail: response.getContentText()
    });

  } catch (err) {
    return jsonResponse({ error: err.message });
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * สร้างหรือค้นหา folder hierarchy
 * folderPath เช่น "LAMY/2568/EQ-001"  →  สร้างแต่ละ level ถ้ายังไม่มี
 */
function getOrCreateFolder(folderPath) {
  var parts   = folderPath.split('/').filter(function(p) { return p.length > 0; });
  var current = DriveApp.getRootFolder();
  parts.forEach(function(part) {
    var iter = current.getFoldersByName(part);
    current  = iter.hasNext() ? iter.next() : current.createFolder(part);
  });
  return current;
}
