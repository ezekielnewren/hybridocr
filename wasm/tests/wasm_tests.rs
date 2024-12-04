use hybridocr::_argon2id;

#[cfg(test)]
mod tests {
    use std::time::Instant;
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
}
