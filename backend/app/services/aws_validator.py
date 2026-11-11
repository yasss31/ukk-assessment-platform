"""
app/services/aws_validator.py - Validasi Kredensial AWS (STS GetCallerIdentity)
"""
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from app.models.schemas import AWSCredentialInput, AWSCredentialValidationResult


class AWSValidator:
    @staticmethod
    def validate_credentials(creds: AWSCredentialInput) -> AWSCredentialValidationResult:
        """
        Validasi kredensial AWS Academy secara aman menggunakan AWS STS GetCallerIdentity.
        Kredensial hanya diproses di memori dan tidak disimpan ke disk/database.
        """
        region = creds.aws_region or "us-east-1"
        try:
            session = boto3.Session(
                aws_access_key_id=creds.aws_access_key_id,
                aws_secret_access_key=creds.aws_secret_access_key,
                aws_session_token=creds.aws_session_token,
                region_name=region
            )
            sts = session.client("sts")
            identity = sts.get_caller_identity()
            
            return AWSCredentialValidationResult(
                is_valid=True,
                account_id=identity.get("Account"),
                arn=identity.get("Arn"),
                region=region,
                error_message=None
            )
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            if code in ["ExpiredToken", "RequestExpired"]:
                err = "Kredensial sesi AWS Academy telah kedaluwarsa (Expired Token). Silakan salin kredensial baru."
            elif code in ["AuthFailure", "InvalidClientTokenId", "SignatureDoesNotMatch"]:
                err = f"Kredensial AWS tidak valid ({code}). Periksa kembali Access Key, Secret Key, dan Session Token."
            elif code == "AccessDenied":
                err = "Akses ditolak (AccessDenied) saat memanggil AWS STS."
            else:
                err = f"Gagal autentikasi AWS ({code}): {msg}"
            return AWSCredentialValidationResult(
                is_valid=False,
                account_id=None,
                arn=None,
                region=region,
                error_message=err
            )
        except EndpointConnectionError:
            return AWSCredentialValidationResult(
                is_valid=False,
                account_id=None,
                arn=None,
                region=region,
                error_message="Gagal terhubung ke endpoint AWS STS. Periksa koneksi internet."
            )
        except Exception as e:
            return AWSCredentialValidationResult(
                is_valid=False,
                account_id=None,
                arn=None,
                region=region,
                error_message=f"Terjadi kesalahan saat validasi AWS: {str(e)}"
            )

