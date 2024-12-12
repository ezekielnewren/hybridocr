use std::path::{Path};
use image::{ImageReader, DynamicImage, ImageFormat, ImageBuffer, GrayImage, Luma, RgbImage, Rgb, RgbaImage, Rgba};
use hybridocr::{_argon2id, util::_pt};
use std::fs::File;
use std::io::{Cursor, Write};
use std::time::Instant;
use imageproc::geometric_transformations::{warp_into, Interpolation, Projection};
use hybridocr::util::{PixelBuffer, Quadrilateral, Point, transpose};

pub fn write_image(img: DynamicImage, fmt: ImageFormat, path: &Path) {
    let mut bytes = Vec::<u8>::new();
    let mut buffer = Cursor::new(&mut bytes);
    let _ = img.write_to(&mut buffer, fmt);

    let mut fdo = File::create(path).unwrap();
    fdo.write(bytes.as_slice()).unwrap();
}



pub fn get_transform(proj: &Projection) -> Vec<[f32; 9]> {
    let mut out = Vec::<[f32; 9]>::new();
    unsafe {
        let ptr = proj as *const Projection;
        let x = ptr as *const [f32; 9];
        out.push(*x.add(0));
        out.push(*x.add(1));
    }
    out
}


pub fn from_dynamic_image(img: &DynamicImage) -> PixelBuffer {
    PixelBuffer::new(
        img.width() as usize,
        img.height() as usize,
        img.color().channel_count() as usize,
        true,
        img.as_bytes()
    ).unwrap()
}

pub fn as_bytes(pb: &PixelBuffer) -> Vec<u8> {
    if pb.interleaved {
        pb.data.clone()
    } else {
        let mut t = vec![0u8; pb.data.len()];
        let w = pb.width*pb.height;
        let h = pb.channels;
        transpose(pb.data.as_slice(), w, h, t.as_mut_slice()).unwrap();
        t
    }
}

pub fn as_dynamic_image(pb: &PixelBuffer) -> Result<DynamicImage, String> {
    let woven = as_bytes(&pb);

    if pb.channels == 1 {
        Ok(DynamicImage::ImageLuma8(ImageBuffer::from_vec(pb.width as u32, pb.height as u32, woven).unwrap()))
    } else if pb.channels == 2 {
        Ok(DynamicImage::ImageLumaA8(ImageBuffer::from_vec(pb.width as u32, pb.height as u32, woven).unwrap()))
    } else if pb.channels == 3 {
        Ok(DynamicImage::ImageRgb8(ImageBuffer::from_vec(pb.width as u32, pb.height as u32, woven).unwrap()))
    } else if pb.channels == 4 {
        Ok(DynamicImage::ImageRgba8(ImageBuffer::from_vec(pb.width as u32, pb.height as u32, woven).unwrap()))
    } else {
        Err(String::from("Illegal parameters"))
    }
}


pub fn as_array(quad: &Quadrilateral) -> [(f32, f32); 4] {
    [(quad.tl.x, quad.tl.y), (quad.tr.x, quad.tr.y), (quad.br.x, quad.br.y), (quad.bl.x, quad.bl.y)]
}


pub fn dst_rect(quad: &Quadrilateral) -> [(f32, f32); 4] {
    let (width, height) = quad.output_dimension();

    [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]
}

pub fn _perspective_transform(pb: &PixelBuffer, quad: &Quadrilateral) -> Result<PixelBuffer, String> {
    let projection = Projection::from_control_points(as_array(&quad), dst_rect(&quad)).unwrap();
    let out_dim = quad.output_dimension();
    let w = out_dim.0 as u32;
    let h = out_dim.1 as u32;

    let src = as_bytes(&pb);
    let out_img: DynamicImage;
    if pb.channels == 1 {
        let gray = GrayImage::from_vec(pb.width as u32, pb.height as u32, src).unwrap();
        let dp = Luma([0]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &gray,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else if pb.channels == 3 {
        let rgb = RgbImage::from_vec(pb.width as u32, pb.height as u32, src).unwrap();
        let dp = Rgb([0, 0, 0]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &rgb,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else if pb.channels == 4 {
        let rgba = RgbaImage::from_vec(pb.width as u32, pb.height as u32, src).unwrap();
        let dp = Rgba([0u8, 0u8, 0u8, 0u8]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &rgba,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else {
        return Err(String::from("only 1, 3, or 4 channels are supported"));
    }

    let mut pb_out = from_dynamic_image(&out_img);
    if !pb.interleaved {
        pb_out.toggle_interleaved();
    }
    Ok(pb_out)
}

#[cfg(test)]
mod tests {
    use imageproc::drawing::Canvas;
    use imageproc::geometric_transformations::Projection;
    use hybridocr::util::{calculate_homography_matrix, FloatBuffer};
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

        let mut pb = from_dynamic_image(&img);
        pb.toggle_interleaved();
        assert_eq!(pb.width*pb.height*pb.channels, pb.data.len());
        let interleaved = pb.interleaved;

        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };


        let result = _pt(pb, quad).unwrap();
        let out = as_dynamic_image(&result).unwrap();

        assert_eq!(interleaved, result.interleaved);
        write_image(out, ImageFormat::Png, Path::new("/tmp/output.png"));
    }

    #[test]
    pub fn test_custom_pt() {
        let fd = ImageReader::open("../tests/file/ocr_sample_from_smartphone_rgba.avif").unwrap();
        let img_rgba = fd.decode().unwrap();
        let _img_rgb = DynamicImage::ImageRgb8(img_rgba.to_rgb8());
        let img_gray = DynamicImage::ImageLuma8(img_rgba.to_luma8());
        let img = &img_gray;

        let pb = from_dynamic_image(&img);
        let src_interleaved = pb.interleaved;
        assert_eq!(pb.width*pb.height*pb.channels, pb.data.len());

        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };

        let start = Instant::now();
        let result = _pt(pb, quad).unwrap();
        let t = start.elapsed();
        let view = t.as_millis();
        assert!(view > 0);
        let out = as_dynamic_image(&result).unwrap();


        assert_eq!(src_interleaved, result.interleaved);
        write_image(out, ImageFormat::Png, Path::new("/tmp/output.png"));
    }

    #[test]
    pub fn test_homography_matrix() {
        let quad = Quadrilateral {
            tl: Point{x: 50.0,   y: 335.0},
            tr: Point{x: 1076.0, y: 305.0},
            br: Point{x: 1130.0, y: 1688.0},
            bl: Point{x: 29.0,   y: 1690.0},
        };
        let src = as_array(&quad);
        let dst = dst_rect(&quad);
        let projection = Projection::from_control_points(src, dst).unwrap();
        let result = get_transform(&projection);
        let transform = result[0];
        let inverse = result[1];
        assert_ne!(transform, inverse);

        let d = quad.dst_quad();
        let mat = calculate_homography_matrix(&d, &quad);

        // assert_eq!(inverse, mat);
    }

    #[test]
    pub fn test_float_buffer() {
        let x: Vec<u8> = vec![
            0xa0, 0xb0, 0xc0, 0xa1, 0xb1, 0xc1, 0xa2, 0xb2, 0xc2,
            0xa3, 0xb3, 0xc3, 0xa4, 0xb4, 0xc4, 0xa5, 0xb5, 0xc5,
            0xa6, 0xb6, 0xc6, 0xa7, 0xb7, 0xc7, 0xa8, 0xb8, 0xc8,
            0xa9, 0xb9, 0xc9, 0xaa, 0xba, 0xca, 0xab, 0xbb, 0xcb,
            0xac, 0xbc, 0xcc, 0xad, 0xbd, 0xcd, 0xae, 0xbe, 0xce,
        ];

        let mut pb = PixelBuffer::new(3, 5, 3, true, x.as_slice()).unwrap();
        // pb.toggle_interleaved();

        let fb = FloatBuffer::from_pixel_buffer(pb, 2);

        assert!(fb.width > 0);
    }

}
