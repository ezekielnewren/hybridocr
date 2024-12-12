use std::time::Instant;
use image::{DynamicImage, ImageReader};
use hybridocr::util::{PixelBuffer, Point, Quadrilateral, _pt};




pub fn main() {
    let fd = ImageReader::open("../tests/file/ocr_sample_from_smartphone_rgba.avif").unwrap();
    let img = fd.decode().unwrap();

    let pb = PixelBuffer::new(
        img.width() as usize,
        img.height() as usize,
        img.color().channel_count() as usize,
        true,
        img.as_bytes()
    ).unwrap();

    let quad = Quadrilateral {
        tl: Point{x: 50.0,   y: 335.0},
        tr: Point{x: 1076.0, y: 305.0},
        br: Point{x: 1130.0, y: 1688.0},
        bl: Point{x: 29.0,   y: 1690.0},
    };

    let start = Instant::now();
    let result = _pt(pb, quad).unwrap();
    let t = start.elapsed();
    let view = t.as_secs_f32();
    println!("seconds: {}", view);
}
