#!/usr/bin/env python3
"""
PIN_COMPARE_V2_REWRITE.py — self-contained.
Full clean rewrite: replaces PINPhotoCompareSheet + dead PINComparePickerSheet
with a two-screen flow (grid picker -> comparison view w/ Share + Download).
Boundaries found by NAME, robust to line drift.
"""
import sys
from pathlib import Path

PATH = Path("/Users/philipmcgarry/Desktop/PIN/PIN/PINProgressPhotos.swift")

NEW_BLOCK = r"""struct PINPhotoCompareSheet: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var store: PINPhotoStore

    // PIN-COMPARE-V2: up to two selected photos, in tap order.
    // selected[0] = Before, selected[1] = After.
    @State private var selected: [PINProgressPhoto] = []
    @State private var showingComparison = false

    // export
    @State private var shareImage: UIImage? = nil
    @State private var showShare = false
    @State private var saveConfirm = false

    var body: some View {
        ZStack {
            Color(hex: "0f0e0c").ignoresSafeArea()
            if showingComparison {
                comparisonScreen
            } else {
                pickerScreen
            }
        }
        .sheet(isPresented: $showShare) {
            if let img = shareImage { PINShareSheet(items: [img]) }
        }
        .alert("Saved to Photos", isPresented: $saveConfirm) {
            Button("OK", role: .cancel) { }
        } message: {
            Text("Your comparison image is in your camera roll.")
        }
    }

    // MARK: Screen 1 — pick two photos

    var pickerScreen: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                RoundedRectangle(cornerRadius: 2).fill(Color(hex: "3a3630"))
                    .frame(width: 36, height: 3).padding(.top, 14)
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Side-by-side compare").font(.system(size: 18, weight: .heavy)).foregroundColor(Color(hex: "f5f0e8"))
                        Text(pickerHint).font(.system(size: 12)).foregroundColor(Color(hex: "6b6259"))
                    }
                    Spacer()
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark").foregroundColor(Color(hex: "a89f94")).font(.system(size: 11))
                            .frame(width: 30, height: 30).background(Color(hex: "221f1b")).cornerRadius(8)
                    }
                }
                .padding(.horizontal, 18).padding(.vertical, 14)
                .overlay(Rectangle().fill(Color(hex: "2d2925")).frame(height: 0.5), alignment: .bottom)
            }

            if store.photos.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "photo.on.rectangle").foregroundColor(Color(hex: "3a3630")).font(.system(size: 32))
                    Text("No photos yet").font(.system(size: 13, weight: .bold)).foregroundColor(Color(hex: "6b6259"))
                    Text("Add progress photos first, then compare.")
                        .font(.system(size: 11)).foregroundColor(Color(hex: "3a3630")).multilineTextAlignment(.center)
                }.padding(.horizontal, 40)
                Spacer()
            } else {
                ScrollView {
                    LazyVGrid(columns: [GridItem(.flexible(), spacing: 6), GridItem(.flexible(), spacing: 6), GridItem(.flexible(), spacing: 6)], spacing: 6) {
                        ForEach(store.photos) { photo in
                            pickerCell(photo)
                        }
                    }.padding(12)
                }
            }

            // View comparison button
            let ready = selected.count == 2
            Button(action: { if ready { showingComparison = true } }) {
                HStack(spacing: 7) {
                    Image(systemName: "eye").font(.system(size: 14, weight: .bold))
                    Text("View comparison").font(.system(size: 15, weight: .heavy))
                }
                .foregroundColor(Color(hex: ready ? "0f0e0c" : "6b6259"))
                .frame(maxWidth: .infinity).padding(.vertical, 14)
                .background(Color(hex: ready ? "7ee8a2" : "2d2925")).cornerRadius(11)
            }
            .disabled(!ready)
            .padding(.horizontal, 12).padding(.bottom, 14).padding(.top, 4)
        }
    }

    var pickerHint: String {
        switch selected.count {
        case 0: return "Tap two photos — first is Before, second is After"
        case 1: return "Now tap your After photo"
        default: return "Ready — tap View comparison"
        }
    }

    func pickerCell(_ photo: PINProgressPhoto) -> some View {
        let idx = selected.firstIndex(of: photo)
        let isSel = idx != nil
        let order = idx.map { $0 + 1 }
        return Button(action: { toggle(photo) }) {
            ZStack {
                if let img = store.image(for: photo) {
                    Image(uiImage: img).resizable().aspectRatio(contentMode: .fill)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    Rectangle().fill(Color(hex: "221f1b"))
                }
                // date, bottom-left
                VStack {
                    Spacer()
                    HStack {
                        Text(formatDate(photo.dateTaken))
                            .font(.system(size: 9, weight: .bold)).foregroundColor(Color(hex: "f5f0e8"))
                            .padding(.horizontal, 5).padding(.vertical, 2)
                            .background(Color(hex: "0f0e0c").opacity(0.85)).cornerRadius(4)
                        Spacer()
                    }
                }.padding(5)
                // selection number + tag
                if let order = order {
                    VStack {
                        HStack {
                            Text(order == 1 ? "BEFORE" : "AFTER")
                                .font(.system(size: 8, weight: .bold)).foregroundColor(Color(hex: "0f0e0c"))
                                .padding(.horizontal, 5).padding(.vertical, 2)
                                .background(Color(hex: "7ee8a2").opacity(0.92)).cornerRadius(4)
                            Spacer()
                            Text("\(order)")
                                .font(.system(size: 11, weight: .heavy)).foregroundColor(Color(hex: "0f0e0c"))
                                .frame(width: 22, height: 22).background(Color(hex: "7ee8a2")).clipShape(Circle())
                        }
                        Spacer()
                    }.padding(5)
                }
            }
            .aspectRatio(1, contentMode: .fill)
            .frame(maxWidth: .infinity)
            .clipped()
            .cornerRadius(10)
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color(hex: isSel ? "7ee8a2" : "2d2925"), lineWidth: isSel ? 2.5 : 0.5))
        }
        .buttonStyle(.plain)
    }

    func toggle(_ photo: PINProgressPhoto) {
        if let i = selected.firstIndex(of: photo) {
            selected.remove(at: i)
        } else if selected.count < 2 {
            selected.append(photo)
        }
    }

    // MARK: Screen 2 — view comparison

    var comparisonScreen: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                RoundedRectangle(cornerRadius: 2).fill(Color(hex: "3a3630"))
                    .frame(width: 36, height: 3).padding(.top, 14)
                HStack(spacing: 10) {
                    Button(action: { showingComparison = false }) {
                        HStack(spacing: 3) {
                            Image(systemName: "chevron.left").font(.system(size: 13, weight: .bold))
                            Text("Back").font(.system(size: 14, weight: .bold))
                        }.foregroundColor(Color(hex: "7ee8a2"))
                    }
                    Text("Your comparison").font(.system(size: 16, weight: .heavy)).foregroundColor(Color(hex: "f5f0e8"))
                    Spacer()
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark").foregroundColor(Color(hex: "a89f94")).font(.system(size: 11))
                            .frame(width: 30, height: 30).background(Color(hex: "221f1b")).cornerRadius(8)
                    }
                }
                .padding(.horizontal, 18).padding(.vertical, 14)
                .overlay(Rectangle().fill(Color(hex: "2d2925")).frame(height: 0.5), alignment: .bottom)
            }

            if selected.count == 2 {
                HStack(spacing: 3) {
                    comparisonHalf(selected[0], label: "BEFORE", alignRight: false)
                    comparisonHalf(selected[1], label: "AFTER", alignRight: true)
                }
                .frame(height: 380)
                .clipped()
                .cornerRadius(12)
                .padding(.horizontal, 14).padding(.top, 14)

                Text("Exports at 1080 × 1350 for Instagram")
                    .font(.system(size: 10)).foregroundColor(Color(hex: "6b6259"))
                    .padding(.top, 8)

                HStack(spacing: 8) {
                    Button(action: { shareComposite() }) {
                        HStack(spacing: 6) {
                            Image(systemName: "square.and.arrow.up").font(.system(size: 14, weight: .bold))
                            Text("Share").font(.system(size: 15, weight: .heavy))
                        }
                        .foregroundColor(Color(hex: "0f0e0c"))
                        .frame(maxWidth: .infinity).padding(.vertical, 13)
                        .background(Color(hex: "7ee8a2")).cornerRadius(11)
                    }
                    Button(action: { saveComposite() }) {
                        HStack(spacing: 6) {
                            Image(systemName: "square.and.arrow.down").font(.system(size: 14, weight: .bold))
                            Text("Download").font(.system(size: 15, weight: .heavy))
                        }
                        .foregroundColor(Color(hex: "f5f0e8"))
                        .frame(maxWidth: .infinity).padding(.vertical, 13)
                        .background(Color(hex: "221f1b")).cornerRadius(11)
                        .overlay(RoundedRectangle(cornerRadius: 11).stroke(Color(hex: "2d2925"), lineWidth: 0.5))
                    }
                }
                .padding(.horizontal, 14).padding(.top, 14)
            }
            Spacer()
        }
    }

    func comparisonHalf(_ photo: PINProgressPhoto, label: String, alignRight: Bool) -> some View {
        ZStack {
            if let img = store.image(for: photo) {
                Image(uiImage: img).resizable().aspectRatio(contentMode: .fill)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Rectangle().fill(Color(hex: "221f1b"))
            }
            VStack {
                HStack {
                    if alignRight { Spacer() }
                    Text(formatDate(photo.dateTaken))
                        .font(.system(size: 10, weight: .bold)).foregroundColor(.white)
                        .padding(.horizontal, 7).padding(.vertical, 3)
                        .background(Color.black.opacity(0.7)).cornerRadius(100)
                    if !alignRight { Spacer() }
                }
                Spacer()
                HStack {
                    if alignRight { Spacer() }
                    Text(label)
                        .font(.system(size: 9, weight: .bold)).foregroundColor(Color(hex: "0f0e0c"))
                        .padding(.horizontal, 7).padding(.vertical, 3)
                        .background(Color(hex: "7ee8a2").opacity(0.92)).cornerRadius(100)
                    if !alignRight { Spacer() }
                }
            }.padding(8)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .clipped()
    }

    // MARK: export

    private func buildComposite() -> UIImage? {
        guard selected.count == 2,
              let limg = store.image(for: selected[0]),
              let rimg = store.image(for: selected[1]) else { return nil }
        return PINStitchRenderer.makeComposite(
            left: limg, right: rimg,
            leftDate: selected[0].dateTaken, rightDate: selected[1].dateTaken
        )
    }

    private func shareComposite() {
        guard let img = buildComposite() else { return }
        shareImage = img
        showShare = true
    }

    private func saveComposite() {
        guard let img = buildComposite() else { return }
        UIImageWriteToSavedPhotosAlbum(img, nil, nil, nil)
        saveConfirm = true
    }

    func formatDate(_ d: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "MMM d, yyyy"
        return f.string(from: d)
    }
}
"""

txt = PATH.read_text()
lines = txt.split("\n")

start = end = None
for i, ln in enumerate(lines):
    if ln.startswith("struct PINPhotoCompareSheet"):
        start = i
    if ln.startswith("struct PINPhotosPINMAXXUpsell"):
        end = i
        break

if start is None or end is None:
    print(f"ABORTING - boundaries not found (start={start}, end={end})"); sys.exit(1)

keep_from = end
j = end - 1
while j > start and (lines[j].strip().startswith("//") or lines[j].strip() == ""):
    keep_from = j
    j -= 1

before = "\n".join(lines[:start])
after = "\n".join(lines[keep_from:])
new_txt = before + "\n" + NEW_BLOCK + "\n" + after

(PATH.parent / (PATH.name + ".backup_before_compare_v2")).write_text(txt)
print("OK Backup:", PATH.name + ".backup_before_compare_v2")
PATH.write_text(new_txt)

b = new_txt.count("{") - new_txt.count("}")
p = new_txt.count("(") - new_txt.count(")")
k = new_txt.count("[") - new_txt.count("]")
print(f"Whole-file balance -> brace {b}, paren {p}, bracket {k}")
print("balanced" if (b==0 and p==0 and k==0) else "!!! NOT BALANCED - review")
print("old picker removed:", "struct PINComparePickerSheet" not in new_txt)
print("pickerScreen present:", "var pickerScreen" in new_txt)
print("comparisonScreen present:", "var comparisonScreen" in new_txt)
print("upsell intact:", "struct PINPhotosPINMAXXUpsell" in new_txt)
print()
print("COMPARE V2 REWRITE DONE")
print()
print("XCODE: Cmd+Shift+K, Cmd+B, Cmd+R")
print()
print("VERIFY:")
print("  1. Compare -> grid of ALL photos.")
print("  2. Tap one -> green ring + 1 BEFORE. Tap another -> 2 AFTER. No zoom.")
print("  3. View comparison (green) -> tap.")
print("  4. Screen 2: side by side, Share + Download.")
print("  5. Download -> Saved. Share -> share sheet w/ 1080x1350.")
print("  6. Back -> grid, selections intact.")
