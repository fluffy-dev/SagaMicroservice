import pytest
from unittest.mock import AsyncMock

from datetime import datetime, timezone

from src.auth.service.auth import AuthService
from src.auth.service.password import PasswordService
from src.auth.exceptions.auth import CredentialsException
from src.auth.dependencies.user.service import IUserService
from src.auth.dependencies.token.service import ITokenService
from src.auth.dependencies.session.service import ISessionService
from src.auth.dto import (
    LoginDTO,
    TokenPairDTO,
    AccessTokenDTO,
    RefreshTokenDTO,
    UserSessionInfoDTO,
)

from tests.factories import BaseUserDTOFactory

pytestmark = pytest.mark.asyncio


# async def test_login_success(mocker):
#     # Arrange
#     mock_user_service = AsyncMock(spec=IUserService)
#     mock_token_service = AsyncMock(spec=ITokenService)
#     mock_session_service = AsyncMock(spec=ISessionService)
#
#     user_dto = BaseUserDTOFactory.build(
#         password=PasswordService.get_password_hash("secret")
#     )
#     mock_user_service.find.return_value = user_dto
#
#     mock_token_service.generate_access_token.return_value = AccessTokenDTO(token="acc")
#     mock_token_service.generate_refresh_token.return_value = RefreshTokenDTO(
#         token="ref", jti="", expire=datetime.now(timezone.utc)
#     )
#
#     expected_tokens = TokenPairDTO(access_token="acc", refresh_token="ref")
#
#     service = AuthService(mock_user_service, mock_token_service, mock_session_service)
#     login_dto = LoginDTO(login=user_dto.login, password="secret")
#
#     # Act
#     result = await service.login(login_dto, UserSessionInfoDTO())
#
#     # Assert
#     assert result == expected_tokens


async def test_login_wrong_password_raises_exception(mocker):
    # Arrange
    mock_user_service = AsyncMock(spec=IUserService)
    mock_token_service = AsyncMock(spec=ITokenService)
    mock_session_service = AsyncMock(spec=ISessionService)

    # FIX: Use BaseUserDTOFactory
    user_dto = BaseUserDTOFactory.build(
        password=PasswordService.get_password_hash("correct_password")
    )
    mock_user_service.find.return_value = user_dto

    service = AuthService(mock_user_service, mock_token_service, mock_session_service)
    login_dto = LoginDTO(login=user_dto.login, password="wrong_password")

    # Act & Assert
    with pytest.raises(CredentialsException):
        await service.login(login_dto, UserSessionInfoDTO())


async def test_login_user_not_found(mocker):
    mock_user_service = AsyncMock(spec=IUserService)
    mock_user_service.find.return_value = None
    mock_session_service = AsyncMock(spec=ISessionService)

    service = AuthService(mock_user_service, AsyncMock(), mock_session_service)
    login_dto = LoginDTO(login="ghost", password="pw")

    with pytest.raises(CredentialsException):
        await service.login(login_dto, UserSessionInfoDTO())
