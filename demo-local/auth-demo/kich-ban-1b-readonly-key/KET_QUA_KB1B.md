# KẾT QUẢ KỊCH BẢN 1B: READ-ONLY KEY CHI TIẾT (16 TEST CASES)

> Ngày chạy: ___/___/2024
> Người thực hiện: _______________
> Phiên bản Qdrant: v1.12.0

---

## Setup

```
docker compose ps:
NAME               IMAGE                   COMMAND             SERVICE       CREATED        STATUS                  PORTS
qdrant-auth-demo   qdrant/qdrant:v1.12.0   "./entrypoint.sh"   qdrant-auth   1 second ago   Up Less than a second   0.0.0.0:6380->6333/tcp, [::]:6380->6333/tcp, 0.0.0.0:6381->6334/tcp, [::]:6381->6334/tcp
setup_collection.py output:
SETUP COLLECTION CHO AUTH DEMO
============================================================

[1/4] Xóa collection cũ (nếu tồn tại)...
  ✅ Done

[2/4] Tạo collection 'auth_demo'...
  ✅ Collection created

[3/4] Tạo payload indexes...
  ✅ Index: doc_status
  ✅ Index: domain
  ✅ Index: department
  ✅ Index: doc_type

[4/4] Upsert data từ sample_data...
  ✅ points_batch_01.json: 6 points
  ✅ points_batch_02.json: 6 points

============================================================
✅ HOÀN TẤT! Collection 'auth_demo' có 12 points.
============================================================
generate_query.py output:
  Câu hỏi: 'Chính sách bảo mật'
```
[1/2] Sinh Hybrid Search body (dense + sparse + RRF)...
  ✅ Saved: query_hybrid.json
[2/2] Sinh Dense Search body...
  ✅ Saved: query_dense.json

==================================================
✅ Đã lưu 2 file query vào: D:\Qdrant\demo-local\auth-demo\queries
   - query_hybrid.json (hybrid search)
   - query_dense.json  (dense only)


==================================================
---

## PHẦN A: TEST ĐỌC (phải thành công)

### Test 1: Liệt kê collections

```
Kết quả:
{"result":{"collections":[{"name":"auth_demo"}]},"status":"ok","time":5.323e-6}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 2: Chi tiết collection

```
Kết quả:
{"result":{"status":"green","optimizer_status":"ok","indexed_vectors_count":12,"points_count":12,"segments_count":2,"config":{"params":{"vectors":{"dense":{"size":384,"distance":"Cosine"}},"shard_number":1,"replication_factor":1,"write_consistency_factor":1,"on_disk_payload":true,"sparse_vectors":{"keywords":{}}},"hnsw_config":{"m":16,"ef_construct":100,"full_scan_threshold":10000,"max_indexing_threads":0,"on_disk":false},"optimizer_config":{"deleted_threshold":0.2,"vacuum_min_vector_number":1000,"default_segment_number":0,"max_segment_size":null,"memmap_threshold":null,"indexing_threshold":20000,"flush_interval_sec":5,"max_optimization_threads":null},"wal_config":{"wal_capacity_mb":32,"wal_segments_ahead":0},"quantization_config":null,"strict_mode_config":{"enabled":false}},"payload_schema":{"doc_type":{"data_type":"keyword","points":12},"doc_status":{"data_type":"keyword","points":12},"domain":{"data_type":"keyword","points":12},"department":{"data_type":"keyword","points":12}}},"status":"ok","time":0.00024743}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 3: Dense search

```
Kết quả:
{"result":{"points":[{"id":4,"version":8,"score":0.84599,"payload":{"document_id":"DOC-004","title":"Chính sách bảo mật","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Tài liệu nội bộ chỉ được chia sẻ trong phạm vi công việc và phải được bảo vệ bằng mật khẩu."}},{"id":10,"version":9,"score":0.66372424,"payload":{"document_id":"DOC-010","title":"Hồ sơ nhân sự","domain":"nhan_su","department":"BAN_LE","doc_type":"mau","doc_status":"ACTIVE","text":"Hồ sơ nhân sự phải được lưu trữ theo quy định bảo mật và cập nhật hàng quý."}},{"id":12,"version":9,"score":0.64409184,"payload":{"document_id":"DOC-012","title":"Quy định báo cáo tháng","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Báo cáo tháng cần được gửi đúng hạn vào ngày 5 hàng tháng để đảm bảo tiến độ hoạt động."}},{"id":9,"version":9,"score":0.62985146,"payload":{"document_id":"DOC-009","title":"Chính sách mua sắm","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Yêu cầu mua sắm dưới ngưỡng hạn mức cần có xác nhận của quản lý trực tiếp."}},{"id":5,"version":8,"score":0.61987764,"payload":{"document_id":"DOC-005","title":"Quy trình đặt phòng họp","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"quy_trinh","doc_status":"ACTIVE","text":"Đặt phòng họp cần gửi yêu cầu trước 24 giờ và xác nhận lại lịch trình."}}]},"status":"ok","time":0.002709585}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 4: Hybrid search

```
Kết quả:
{"result":{"points":[{"id":4,"version":8,"score":1.0,"payload":{"document_id":"DOC-004","title":"Chính sách bảo mật","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Tài liệu nội bộ chỉ được chia sẻ trong phạm vi công việc và phải được bảo vệ bằng mật khẩu."}},{"id":10,"version":9,"score":0.5833334,"payload":{"document_id":"DOC-010","title":"Hồ sơ nhân sự","domain":"nhan_su","department":"BAN_LE","doc_type":"mau","doc_status":"ACTIVE","text":"Hồ sơ nhân sự phải được lưu trữ theo quy định bảo mật và cập nhật hàng quý."}},{"id":9,"version":9,"score":0.53333336,"payload":{"document_id":"DOC-009","title":"Chính sách mua sắm","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Yêu cầu mua sắm dưới ngưỡng hạn mức cần có xác nhận của quản lý trực tiếp."}},{"id":12,"version":9,"score":0.4166667,"payload":{"document_id":"DOC-012","title":"Quy định báo cáo tháng","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Báo cáo tháng cần được gửi đúng hạn vào ngày 5 hàng tháng để đảm bảo tiến độ hoạt động."}},{"id":3,"version":8,"score":0.31111112,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}}]},"status":"ok","time":0.00228456}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 5: Search + Filter department

```
Kết quả:
{"result":{"points":[{"id":4,"version":8,"score":0.84599,"payload":{"document_id":"DOC-004","title":"Chính sách bảo mật","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Tài liệu nội bộ chỉ được chia sẻ trong phạm vi công việc và phải được bảo vệ bằng mật khẩu."}},{"id":10,"version":9,"score":0.66372424,"payload":{"document_id":"DOC-010","title":"Hồ sơ nhân sự","domain":"nhan_su","department":"BAN_LE","doc_type":"mau","doc_status":"ACTIVE","text":"Hồ sơ nhân sự phải được lưu trữ theo quy định bảo mật và cập nhật hàng quý."}},{"id":12,"version":9,"score":0.64409184,"payload":{"document_id":"DOC-012","title":"Quy định báo cáo tháng","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Báo cáo tháng cần được gửi đúng hạn vào ngày 5 hàng tháng để đảm bảo tiến độ hoạt động."}},{"id":9,"version":9,"score":0.62985146,"payload":{"document_id":"DOC-009","title":"Chính sách mua sắm","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"chinh_sach","doc_status":"ACTIVE","text":"Yêu cầu mua sắm dưới ngưỡng hạn mức cần có xác nhận của quản lý trực tiếp."}},{"id":5,"version":8,"score":0.61987764,"payload":{"document_id":"DOC-005","title":"Quy trình đặt phòng họp","domain":"hanh_chinh","department":"PHONG_HC","doc_type":"quy_trinh","doc_status":"ACTIVE","text":"Đặt phòng họp cần gửi yêu cầu trước 24 giờ và xác nhận lại lịch trình."}}]},"status":"ok","time":0.00243298}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 6: Scroll (phân trang)

```
Kết quả:
{"result":{"points":[{"id":1,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."}},{"id":2,"payload":{"document_id":"DOC-002","title":"Làm thêm giờ","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Làm thêm giờ phải được trưởng bộ phận phê duyệt trước khi thực hiện."}},{"id":3,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}}],"next_page_offset":4},"status":"ok","time":0.001321329}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 7: Get point by ID

```
Kết quả:
{"result":{"points":[{"id":1,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."}},{"id":2,"payload":{"document_id":"DOC-002","title":"Làm thêm giờ","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Làm thêm giờ phải được trưởng bộ phận phê duyệt trước khi thực hiện."}},{"id":3,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}}],"next_page_offset":4},"status":"ok","time":0.001321329}
D:\Qdrant\demo-local\auth-demo>curl.exe "http://localhost:6380/collections/auth_demo/points/1" -H "api-key: readonly-key-2024"
{"result":{"id":1,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."},"vector":{"keywords":{"indices":[53487911,103616747,227867999,228347099,316267852,683022899,713926814,732467675,757096994,873203361,980622016,1000629648,1087016189,1229554415,1417668429,1433409115,1478999391,1745450706,1849926552,2110423782],"values":[1.5932107,1.5932107,1.5932107,1.8480722,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.9521663,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107,1.5932107]},"dense":[-0.038158845,0.03338899,-0.009026752,-0.037119605,0.046579376,0.0069216206,0.060329348,-0.037199546,-0.016148226,-0.01218445,-0.010532321,-0.07674405,0.052628297,0.0100060385,0.03581389,0.019852193,0.01987884,-0.027952954,-0.033921935,0.027979601,-0.014602687,-0.025981057,-0.006451963,-0.025221612,0.025101699,-0.029924849,0.010532321,-0.02827272,0.0004201104,-0.08473822,0.038958263,0.04295535,0.015708547,-0.0091400035,0.016907673,0.029258668,-0.020305196,-0.03714625,0.012610806,0.017720414,0.020771522,-0.018972835,-0.0487378,-0.06640492,0.09161321,-0.04508713,-0.026034353,-0.026274178,0.06507256,-0.024675343,-0.04236911,0.03448153,0.036027066,0.0579311,0.006272094,-0.010685543,-0.0043601547,0.008733633,0.006795046,-0.04450089,0.02238368,0.022743419,-0.1611625,0.005532633,-0.04111669,-0.028139485,0.017573854,0.0042202566,-0.0011175186,-0.044341005,-0.026007706,0.016361404,0.0031477052,0.0066984496,-0.016014991,0.015855107,-0.043115232,0.039810974,-0.039437912,-0.040876865,0.009286563,0.019599045,-0.0012707402,-0.008407204,-0.007041533,0.0057125017,-0.0010842095,0.021424381,-0.017787032,-0.01881295,0.0482315,0.040903512,0.02311648,0.027926307,0.017906945,0.024049133,0.008966796,-0.08521787,-0.036933072,0.4142047,-0.016667848,0.014296244,-0.024395548,-0.025501408,0.0062754247,0.032642867,0.0116048725,-0.065712094,-0.011651506,0.033602167,-0.0052128662,-0.06731093,0.07024212,-0.060809,-0.070721775,0.009326533,-0.009000105,-0.033762053,0.0023133135,0.00031893415,0.031017387,-0.05001687,-0.015815137,-0.05172229,0.039011557,-0.070135534,0.047618616,0.07605122,0.05094952,0.050256692,0.024955139,-0.07008224,0.04516707,-0.024755286,-0.0035607372,-0.040983453,0.026367443,-0.011378371,0.008713647,-0.048657857,0.05329448,-0.07557157,-0.042422406,-0.061022177,-0.02808619,0.021650882,-0.050709695,0.022183826,-0.014775894,0.0038805043,-0.009339857,0.024582079,0.014496098,-0.0069216206,-0.03330905,-0.026274178,0.06326055,0.052122,-0.028592488,0.0042202566,0.039917566,-0.064592905,0.0017653796,0.06603186,0.0054127206,-0.003220985,-0.0052495063,-0.035014473,0.0386385,-0.07839618,0.06832352,0.01991881,-0.08447175,-0.010299158,0.03613366,-0.0058157598,0.06827023,0.052122,-0.0540406,-0.03418841,-0.058464043,-0.049777042,0.040690333,0.022530241,0.057184976,-0.027873011,-0.020052047,-0.024555432,0.013976477,0.009486417,-0.022610182,0.03871844,-0.010672219,0.019492455,0.01612158,-0.007181431,-0.05489331,-0.005052983,-0.057184976,0.019852193,0.03221651,-0.0656588,-0.03823879,-0.015628606,0.044740714,-0.012797337,-0.04295535,-0.014789218,-0.0073679616,0.10168587,-0.021917354,-0.00041886128,0.011844697,-0.020478403,-0.03011138,0.028059542,-0.025461437,0.0482848,0.048817743,-0.021637559,0.01983887,-0.06768399,0.010918707,-0.28885606,0.020131988,0.03794567,-0.013670034,0.07509192,-0.020145312,-0.005392735,0.018679714,0.093851574,0.043488294,0.023702718,0.029978145,0.0067184353,0.074878745,0.011511607,-0.036746543,0.048044972,-0.05713168,0.00026147603,0.025607998,-0.044101182,0.05675862,-0.040024154,-0.042049345,0.016841056,0.01572187,0.13771293,-0.00143562,0.020131988,0.018200064,0.07498533,0.04383471,-0.055159785,-0.10781473,0.079888426,-0.013843241,-0.05230853,-0.046952434,-0.01741397,-0.058943693,0.052148648,0.0120512135,-0.03357552,-0.089694604,-0.013976477,0.011798065,-0.03986427,0.02587447,-0.10445718,0.05713168,-0.0067450823,-0.009806184,-0.007427918,-0.0113184145,-0.031550333,0.0058590616,-0.053401068,0.0009201625,0.03261622,0.02017196,0.02779307,0.008780265,0.011538254,-0.014229625,-0.009233268,0.016547935,0.072906844,0.0074412418,-0.00038700952,0.07157449,-0.013163736,-0.014629334,-0.047138967,-0.034748,0.019199336,-0.039251383,0.017906945,-0.054786723,0.046286255,-0.033415638,0.053720836,-0.074185915,0.025994381,0.017094204,0.043195173,0.00021359428,0.054200485,0.0010392424,0.07567816,-0.0039138133,-0.043461647,0.030537736,0.020038724,-0.044634126,0.0012557511,-0.00279796,-0.27158865,0.054680135,-0.052335177,0.0936384,-0.01866639,-0.003647341,0.04759197,0.041729577,-0.090120964,0.067790575,0.019425837,0.018053504,0.010605602,-0.06491268,0.018026857,-0.03522765,-0.028512547,0.0023799315,0.04114334,-0.0056891856,0.021810764,0.020531697,0.1244959,0.032029983,-0.0006162174,-0.01708088,0.0041536386,-0.023236392,-0.03887832,-0.037812434,-0.0328294,-0.01237098,0.048684508,-0.013776623,0.041916106,0.065552205,-0.07786323,0.01240429,0.02161091,-0.0074412418,-0.034801293,0.044580832,-0.055372965,0.045140423,0.05675862,-0.0015638599,-0.0149091305,-0.08617717,0.045220364,0.020185284,0.0468192,-0.002558135,0.012943896,0.085004695,0.028166132,0.014789218,-0.003890497,-0.09140003,0.101525985,-0.0791423,0.028485898,0.005052983,0.12023234,0.045993134,0.031070681]}},"status":"ok","time":0.001760936}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 8: Get multiple points

```
Kết quả:
{"result":[{"id":1,"payload":{"document_id":"DOC-001","title":"Quy định nghỉ phép","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Nhân viên được nghỉ phép 12 ngày mỗi năm và có thể chuyển đổi sang nghỉ bù khi cần."}},{"id":2,"payload":{"document_id":"DOC-002","title":"Làm thêm giờ","domain":"nhan_su","department":"BAN_LE","doc_type":"quy_dinh","doc_status":"ACTIVE","text":"Làm thêm giờ phải được trưởng bộ phận phê duyệt trước khi thực hiện."}},{"id":3,"payload":{"document_id":"DOC-003","title":"Hướng dẫn onboarding","domain":"nhan_su","department":"BAN_LE","doc_type":"huong_dan","doc_status":"ACTIVE","text":"Nhân viên mới cần hoàn tất các thủ tục đăng ký tài khoản và cam kết bảo mật thông tin."}}],"status":"ok","time":0.001190185}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 9: Count points

```
Kết quả:
{"result":{"count":12},"status":"ok","time":0.000682072}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

## PHẦN B: TEST GHI (phải bị từ chối 403)

### Test 10: Upsert point

```
Kết quả:
❌ HTTP 403
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000013037}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 11: Delete points

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000013423}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 12: Update payload

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000064137}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 13: Tạo collection mới

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.00001328}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 14: Xóa collection

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000010114}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 15: Tạo index

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000024325}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

### Test 16: Tạo snapshot

```
Kết quả:
{"status":{"error":"Forbidden: Global manage access is required"},"time":0.000183668}
```

| Đúng mong đợi? | ☐ Có | ☐ Không |

---

## Tổng kết

### Phần A - Đọc (mong đợi: 200 OK)

| # | Thao tác | Mong đợi | Thực tế | Pass? |
|---|----------|----------|---------|-------|
| 1 | List collections | 200 | | ☐ |
| 2 | Collection info | 200 | | ☐ |
| 3 | Dense search | 200 | | ☐ |
| 4 | Hybrid search | 200 | | ☐ |
| 5 | Search + filter | 200 | | ☐ |
| 6 | Scroll | 200 | | ☐ |
| 7 | Get by ID | 200 | | ☐ |
| 8 | Get multiple | 200 | | ☐ |
| 9 | Count | 200 | | ☐ |

### Phần B - Ghi (mong đợi: 403 Forbidden)

| # | Thao tác | Mong đợi | Thực tế | Pass? |
|---|----------|----------|---------|-------|
| 10 | Upsert | 403 | | ☐ |
| 11 | Delete points | 403 | | ☐ |
| 12 | Update payload | 403 | | ☐ |
| 13 | Create collection | 403 | | ☐ |
| 14 | Delete collection | 403 | | ☐ |
| 15 | Create index | 403 | | ☐ |
| 16 | Create snapshot | 403 | | ☐ |

**Tổng: ___/16 passed**

---

## Ghi chú / Vấn đề phát sinh

```

```
