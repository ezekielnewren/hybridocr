use hybridocr::{_argon2id, util::_perspective_transform};

#[cfg(test)]
mod tests {
    use std::fs::File;
    use std::io::{Cursor, Write};
    use std::path::Path;
    use std::time::Instant;
    use image::{ImageReader, ImageFormat};
    use hybridocr::util::{PixelBuffer, Quadrilateral, Point};
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
        let fd = ImageReader::open("../tests/file/ocr_sample_from_smartphone.webp").unwrap();
        let img = fd.decode().unwrap();

        let pb = PixelBuffer {
            width: img.width(),
            height: img.height(),
            channels: img.color().channel_count(),
            interleaved: true,
            data: Vec::from(img.as_bytes()),
        };
        assert_eq!((pb.width * pb.height * pb.channels as u32) as usize, pb.data.len());

        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };


        let result = _perspective_transform(pb, quad).unwrap();
        let out = result.as_dynamic_image().unwrap();

        let mut bytes = Vec::<u8>::new();
        let mut buffer = Cursor::new(&mut bytes);
        let _ = out.write_to(&mut buffer, ImageFormat::WebP);

        let mut fdo = File::create(Path::new("/tmp/ocr_sample_from_smartphone_corrected.webp")).unwrap();
        fdo.write(bytes.as_slice()).unwrap();
    }

}
