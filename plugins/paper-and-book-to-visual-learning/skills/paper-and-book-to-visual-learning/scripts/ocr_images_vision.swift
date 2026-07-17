#!/usr/bin/env swift

import AppKit
import Foundation
import Vision

struct OCRResult: Codable {
    let path: String
    let text: String
    let confidence: Float
    let error: String?
}

func recognize(path: String) -> OCRResult {
    guard let image = NSImage(contentsOfFile: path) else {
        return OCRResult(path: path, text: "", confidence: 0, error: "unreadable image")
    }
    var rect = NSRect(origin: .zero, size: image.size)
    guard let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
        return OCRResult(path: path, text: "", confidence: 0, error: "cannot create CGImage")
    }

    var observations: [VNRecognizedTextObservation] = []
    let request = VNRecognizeTextRequest { request, _ in
        observations = request.results as? [VNRecognizedTextObservation] ?? []
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true

    do {
        try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
    } catch {
        return OCRResult(path: path, text: "", confidence: 0, error: String(describing: error))
    }

    let sorted = observations.sorted {
        if abs($0.boundingBox.maxY - $1.boundingBox.maxY) > 0.01 {
            return $0.boundingBox.maxY > $1.boundingBox.maxY
        }
        return $0.boundingBox.minX < $1.boundingBox.minX
    }
    let candidates = sorted.compactMap { $0.topCandidates(1).first }
    let text = candidates.map(\.string).joined(separator: "\n")
    let confidence = candidates.isEmpty ? 0 : candidates.map(\.confidence).reduce(0, +) / Float(candidates.count)
    return OCRResult(path: path, text: text, confidence: confidence, error: nil)
}

let paths = Array(CommandLine.arguments.dropFirst())
let results = paths.map(recognize)
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let data = try encoder.encode(results)
FileHandle.standardOutput.write(data)
