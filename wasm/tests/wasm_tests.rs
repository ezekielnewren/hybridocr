use std::path::{Path};
use image::{ImageReader, DynamicImage, ImageFormat};
use hybridocr::{_argon2id, util::_perspective_transform, util::_pt};
use std::fs::File;
use std::io::{Cursor, Write};
use std::time::Instant;
use hybridocr::util::{PixelBuffer, Quadrilateral, Point};

pub fn write_image(img: DynamicImage, fmt: ImageFormat, path: &Path) {
    let mut bytes = Vec::<u8>::new();
    let mut buffer = Cursor::new(&mut bytes);
    let _ = img.write_to(&mut buffer, fmt);

    let mut fdo = File::create(path).unwrap();
    fdo.write(bytes.as_slice()).unwrap();
}



#[cfg(test)]
mod tests {
    use imageproc::drawing::Canvas;
    use hybridocr::util::Interp;
    use super::*;

    #[test]
    fn test_argon2() {
        let output_length: u32 = 32;
        let password = b"password";
        let salt = b"saltsaltsaltsalt";
        let start = Instant::now();
        let buff = _argon2id(password, salt, 8192, 10, 1, output_length);
        let duration = start.elapsed();

        let result = hex::encode(&buff);
        let expect = "bc0c7ddc954113dafedb32154076459d414b4a38822d39ed9dc668edcf84b6e2";
        assert_eq!(expect, result);

        println!("{}", result);
        println!("{}", duration.as_secs_f64());
    }

    #[test]
    fn test_perspective_transform() {
        let fd = ImageReader::open("../tests/file/ocr_sample_from_smartphone_rgba.avif").unwrap();
        let img_rgba = fd.decode().unwrap();
        let img_rgb = DynamicImage::ImageRgb8(img_rgba.to_rgb8());
        // let img_gray = DynamicImage::ImageLuma8(img_rgba.to_luma8());

        // verify that DynamicImage interleaves the channels into each pixel
        let cs = 3usize;
        let _raw = img_rgb.as_bytes();
        let w = img_rgb.width() as usize;
        let h = img_rgb.height() as usize;
        for row in 0..h {
            for col in 0..w {
                let pixel = img_rgb.get_pixel(col as u32, row as u32);
                for channel in 0..cs {
                    let e = pixel[channel];
                    let pixel_off = row*w+col;
                    let a = _raw[pixel_off*cs+channel];
                    assert_eq!(e, a, "row: {}, col: {}, channel: {}", row, col, channel);
                }
            }
        }

        let img = &img_rgba;

        let mut pb = PixelBuffer::from_dynamic_image(&img);
        pb.toggle_interleaved();
        assert_eq!((pb.width * pb.height * pb.channels as u32) as usize, pb.data.len());

        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };


        let result = _perspective_transform(&pb, &quad).unwrap();
        let out = result.as_dynamic_image().unwrap();

        assert_eq!(pb.interleaved, result.interleaved);
        write_image(out, ImageFormat::Png, Path::new("/tmp/output.png"));
    }

    #[test]
    pub fn test_custom_pt() {
        let fd = ImageReader::open("../tests/file/ocr_sample_from_smartphone_rgba.avif").unwrap();
        let img_rgba = fd.decode().unwrap();
        let img_rgb = DynamicImage::ImageRgb8(img_rgba.to_rgb8());
        let img_gray = DynamicImage::ImageLuma8(img_rgba.to_luma8());
        let img = &img_gray;

        let mut pb = PixelBuffer::from_dynamic_image(&img);
        let src_interleaved = pb.interleaved;
        assert_eq!((pb.width * pb.height * pb.channels as u32) as usize, pb.data.len());

        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };

        let start = Instant::now();
        let result = _pt(pb, quad, Interp::Biquadratic as isize).unwrap();
        let t = start.elapsed();
        let view = t.as_millis();
        let out = result.as_dynamic_image().unwrap();


        assert_eq!(src_interleaved, result.interleaved);
        write_image(out, ImageFormat::Png, Path::new("/tmp/output.png"));
    }

}
