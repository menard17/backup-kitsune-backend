from unittest.mock import Mock

from fhir.resources.patient import Patient

from services.orca_service import OrcaService

PATIENT_DATA = {
    "address": [
        {
            "city": "港区",
            "country": "JP",
            "line": ["1-1-1"],
            "postalCode": "111-1111",
            "state": "東京都",
            "type": "both",
            "use": "home",
        },
        {
            "city": "港区",
            "country": "JP",
            "line": ["2-2-2"],
            "postalCode": "222-2222",
            "state": "東京都",
            "type": "both",
            "use": "work",
        },
    ],
    "birthDate": "2020-08-20",
    "extension": [
        {"url": "stripe-customer-id", "valueString": "test-customer-id"},
        {
            "url": "stripe-payment-method-id",
            "valueString": "test-payment-method-id",
        },
        {
            "url": "fcm-token",
            "valueString": "test-fcm-token",
        },
    ],
    "gender": "female",
    "id": "02989bec-b084-47d9-99fd-259ac6f3360c",
    "meta": {
        "lastUpdated": "2022-09-15T14:04:19.651495+00:00",
        "versionId": "MTY2MzI1MDY1OTY1MTQ5NTAwMA",
    },
    "name": [
        {
            "family": "Official",
            "given": ["Name"],
            "use": "official",
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "IDE",
                },
            ],
        },
        {
            "family": "Unofficial",
            "given": ["Name"],
            "use": "temp",
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "ABC",
                },
            ],
        },
        {
            "family": "kanaFamilyName",
            "given": ["kanaGivenName"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "SYL",
                },
            ],
        },
    ],
    "resourceType": "Patient",
    "telecom": [
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "home",
            "value": "home-email@gmail.com",
        },
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "work",
            "value": "work-email@gmail.com",
        },
        {"system": "phone", "use": "mobile", "value": "08011111111"},
    ],
}

PATIENT_DATA_WITHOUT_DOB_AND_GENDER = {
    "address": [
        {
            "city": "港区",
            "country": "JP",
            "line": ["1-1-1"],
            "postalCode": "111-1111",
            "state": "東京都",
            "type": "both",
            "use": "home",
        },
        {
            "city": "港区",
            "country": "JP",
            "line": ["2-2-2"],
            "postalCode": "222-2222",
            "state": "東京都",
            "type": "both",
            "use": "work",
        },
    ],
    "extension": [
        {"url": "stripe-customer-id", "valueString": "test-customer-id"},
        {
            "url": "stripe-payment-method-id",
            "valueString": "test-payment-method-id",
        },
        {
            "url": "fcm-token",
            "valueString": "test-fcm-token",
        },
    ],
    "id": "02989bec-b084-47d9-99fd-259ac6f3360c",
    "meta": {
        "lastUpdated": "2022-09-15T14:04:19.651495+00:00",
        "versionId": "MTY2MzI1MDY1OTY1MTQ5NTAwMA",
    },
    "name": [
        {"family": "Official", "given": ["Name"], "use": "official"},
        {"family": "Unofficial", "given": ["Name"], "use": "temp"},
    ],
    "resourceType": "Patient",
    "telecom": [
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "home",
            "value": "home-email@gmail.com",
        },
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "work",
            "value": "work-email@gmail.com",
        },
        {"system": "phone", "use": "mobile", "value": "08011111111"},
    ],
}

TEST_ORCA_PATIENT_NAME = "医療　太郎"
TEST_ORCA_PATIENT_KANA_NAME = "イリョウ　タロウ"
TEST_ORCA_NOT_EXIST_PATIENT_NAME = "侍　太郎"
TEST_ORCA_NOT_EXIST_PATIENT_KANA_NAME = "サムライ　タロウ"
TEST_ORCA_PATIENT_DOB = "2000-08-08"
TEST_ORCA_PATIENT_GENDER = "1"
TEST_ORCA_PATIENT_PHONE_NUMBER = "0332211900"
TEST_ORCA_PATIENT_EMAIL = "aa@example.com"
TEST_ORCA_PATIENT_ZIPCODE = "1740061"
TEST_ORCA_PATIENT_ADDRESS = "東京都板橋区大原町"
TEST_ORCA_PATIENT_STREET_ADDRESS = "44-2"
TEST_ORCA_PATIENT_ID = "00200"
TEST_ORCA_GOVFUND_DATE = "2020-08-08"
TEST_ORCA_GOVFUND_CLASS = "094"
TEST_GOV_FUND_NAME = "コロナ軽症"
TEST_ORCA_GOVFUND_NUM = "28136802"
TEST_ORCA_GOVFUND_PERSON_NUM = "9999996"


class ORCAReplyData:
    pass


TEST_ORCA_CREATE_PATIENT_RETURN_DATA = """<xmlio2>
  <patientmodres type="record">
    <Information_Date type="string">2014-07-17</Information_Date>
    <Information_Time type="string">10:38:30</Information_Time>
    <Api_Result type="string">00</Api_Result>
    <Api_Result_Message type="string">登録終了</Api_Result_Message>
    <Reskey type="string">Acceptance_Info</Reskey>
    <Patient_Information type="record">
      <Patient_ID type="string">00200</Patient_ID>
      <WholeName type="string">日医　太郎</WholeName>
      <WholeName_inKana type="string">ニチイ　タロウ</WholeName_inKana>
      <BirthDate type="string">1970-01-01</BirthDate>
      <Sex type="string">1</Sex>
      <HouseHolder_WholeName type="string">日医　太郎</HouseHolder_WholeName>
      <Relationship type="string">本人</Relationship>
      <Occupation type="string">会社員</Occupation>
      <CellularNumber type="string">09011112222</CellularNumber>
      <FaxNumber type="string">03-0011-2233</FaxNumber>
      <EmailAddress type="string">test@tt.dot.jp</EmailAddress>
      <Home_Address_Information type="record">
        <Address_ZipCode type="string">1130021</Address_ZipCode>
        <WholeAddress1 type="string">東京都文京区本駒込</WholeAddress1>
        <WholeAddress2 type="string">６−１６−３</WholeAddress2>
        <PhoneNumber1 type="string">03-3333-2222</PhoneNumber1>
        <PhoneNumber2 type="string">03-3333-1133</PhoneNumber2>
      </Home_Address_Information>
      <WorkPlace_Information type="record">
        <WholeName type="string">てすと　株式会社</WholeName>
        <Address_ZipCode type="string">1130022</Address_ZipCode>
        <WholeAddress1 type="string">東京都文京区本駒込</WholeAddress1>
        <WholeAddress2 type="string">５−１２−１１</WholeAddress2>
        <PhoneNumber type="string">03-3333-2211</PhoneNumber>
      </WorkPlace_Information>
      <Contraindication1 type="string">状態</Contraindication1>
      <Allergy1 type="string">アレルギ</Allergy1>
      <Infection1 type="string">感染症</Infection1>
      <Comment1 type="string">コメント</Comment1>
      <HealthInsurance_Information type="array">
        <HealthInsurance_Information_child type="record">
          <Insurance_Combination_Number type="string">0001</Insurance_Combination_Number>
          <InsuranceProvider_Class type="string">060</InsuranceProvider_Class>
          <InsuranceProvider_Number type="string">138057</InsuranceProvider_Number>
          <InsuranceProvider_WholeName type="string">国保</InsuranceProvider_WholeName>
          <HealthInsuredPerson_Symbol type="string">０１</HealthInsuredPerson_Symbol>
          <HealthInsuredPerson_Number type="string">１２３４５６７</HealthInsuredPerson_Number>
          <HealthInsuredPerson_Assistance type="string">3</HealthInsuredPerson_Assistance>
          <RelationToInsuredPerson type="string">1</RelationToInsuredPerson>
          <Certificate_StartDate type="string">2010-05-01</Certificate_StartDate>
          <Certificate_ExpiredDate type="string">9999-12-31</Certificate_ExpiredDate>
        </HealthInsurance_Information_child>
        <HealthInsurance_Information_child type="record">
          <Insurance_Combination_Number type="string">0002</Insurance_Combination_Number>
          <InsuranceProvider_Class type="string">060</InsuranceProvider_Class>
          <InsuranceProvider_Number type="string">138057</InsuranceProvider_Number>
          <InsuranceProvider_WholeName type="string">国保</InsuranceProvider_WholeName>
          <HealthInsuredPerson_Symbol type="string">０１</HealthInsuredPerson_Symbol>
          <HealthInsuredPerson_Number type="string">１２３４５６７</HealthInsuredPerson_Number>
          <HealthInsuredPerson_Assistance type="string">3</HealthInsuredPerson_Assistance>
          <RelationToInsuredPerson type="string">1</RelationToInsuredPerson>
          <Certificate_StartDate type="string">2010-05-01</Certificate_StartDate>
          <Certificate_ExpiredDate type="string">9999-12-31</Certificate_ExpiredDate>
          <PublicInsurance_Information type="array">
            <PublicInsurance_Information_child type="record">
              <PublicInsurance_Class type="string">010</PublicInsurance_Class>
              <PublicInsurance_Name type="string">感３７の２</PublicInsurance_Name>
              <PublicInsurer_Number type="string">10131142</PublicInsurer_Number>
              <PublicInsuredPerson_Number type="string">1234566</PublicInsuredPerson_Number>
              <Rate_Admission type="string">0.05</Rate_Admission>
              <Money_Admission type="string">     0</Money_Admission>
              <Rate_Outpatient type="string">0.05</Rate_Outpatient>
              <Money_Outpatient type="string">     0</Money_Outpatient>
              <Certificate_IssuedDate type="string">2010-05-01</Certificate_IssuedDate>
              <Certificate_ExpiredDate type="string">9999-12-31</Certificate_ExpiredDate>
            </PublicInsurance_Information_child>
          </PublicInsurance_Information>
        </HealthInsurance_Information_child>
      </HealthInsurance_Information>
      <Payment_Information type="record">
        <Reduction_Reason type="string">01</Reduction_Reason>
        <Reduction_Reason_Name type="string">低所得</Reduction_Reason_Name>
        <Discount type="string">01</Discount>
        <Discount_Name type="string">10(%)</Discount_Name>
        <Ic_Code type="string">02</Ic_Code>
        <Ic_Code_Name type="string">振込</Ic_Code_Name>
      </Payment_Information>
    </Patient_Information>
  </patientmodres>
</xmlio2>
"""

# Do not change indent for testing
TEST_COMPOSE_CREATE_PATIENT_XML_DATA = f"""
            <data>
                <patientmodreq type="record">
                    <Mod_Key type="string">2</Mod_Key>
                    <Patient_ID type="string">*</Patient_ID>
                    <WholeName type="string">{TEST_ORCA_PATIENT_NAME}</WholeName>
                    <WholeName_inKana type="string">{TEST_ORCA_PATIENT_KANA_NAME}</WholeName_inKana>
                    <BirthDate type="string">{TEST_ORCA_PATIENT_DOB}</BirthDate>
                    <Sex type="string">{TEST_ORCA_PATIENT_GENDER}</Sex>
                    <EmailAddress type="string">{TEST_ORCA_PATIENT_EMAIL}</EmailAddress>
                    <Home_Address_Information type="record">
                        <Address_ZipCode type="string">{TEST_ORCA_PATIENT_ZIPCODE}</Address_ZipCode>
                        <WholeAddress1 type="string">{TEST_ORCA_PATIENT_ADDRESS}</WholeAddress1>
                        <WholeAddress2 type="string">{TEST_ORCA_PATIENT_STREET_ADDRESS}</WholeAddress2>
                        <PhoneNumber1 type="string">{TEST_ORCA_PATIENT_PHONE_NUMBER}</PhoneNumber1>
                    </Home_Address_Information>
                    <HealthInsurance_Information type="record">
                        <PublicInsurance_Information type="array">
                            <PublicInsurance_Information_child type="record">
                                <PublicInsurance_Class type="string">093</PublicInsurance_Class>
                                <PublicInsurance_Name type="string">PCR検査</PublicInsurance_Name>
                                <PublicInsurer_Number type="string">28131399</PublicInsurer_Number>
                                <PublicInsuredPerson_Number type="string">9999996</PublicInsuredPerson_Number>
                                <Certificate_IssuedDate type="string">{TEST_ORCA_GOVFUND_DATE}</Certificate_IssuedDate>
                                <Certificate_ExpiredDate type="string">{TEST_ORCA_GOVFUND_DATE}</Certificate_IssuedDate>
                            </PublicInsurance_Information_child>
                        </PublicInsurance_Information>
                    </HealthInsurance_Information>
                </patientmodreq>
            </data>
            """

VALID_INSCARD_XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<xmlio2>
  <patientinfores type="record">
    <Information_Date type="string">2018-10-02</Information_Date>
    <Information_Time type="string">11:25:31</Information_Time>
    <Api_Result type="string">00</Api_Result>
    <Api_Result_Message type="string">処理終了</Api_Result_Message>
    <Reskey type="string">Patient Info</Reskey>
    <Patient_Information type="record">
      <Patient_ID type="string">00200</Patient_ID>
      <WholeName type="string">てすと　受付</WholeName>
      <WholeName_inKana type="string">テスト　ウケツケ</WholeName_inKana>
      <HealthInsurance_Information type="array">
        <HealthInsurance_Information_child type="record">
          <Insurance_Combination_Number type="string">0001</Insurance_Combination_Number>
          <Certificate_StartDate type="string">2020-01-01</Certificate_StartDate>
          <Certificate_ExpiredDate type="string">9999-01-01</Certificate_ExpiredDate>
        </HealthInsurance_Information_child>
      </HealthInsurance_Information>
    </Patient_Information>
  </patientinfores>
</xmlio2>
"""

INVALID_INSCARD_XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<xmlio2>
  <patientinfores type="record">
    <Information_Date type="string">2018-10-02</Information_Date>
    <Information_Time type="string">11:25:31</Information_Time>
    <Api_Result type="string">00</Api_Result>
    <Api_Result_Message type="string">処理終了</Api_Result_Message>
    <Reskey type="string">Patient Info</Reskey>
    <Patient_Information type="record">
      <Patient_ID type="string">00200</Patient_ID>
      <WholeName type="string">てすと　受付</WholeName>
      <WholeName_inKana type="string">テスト　ウケツケ</WholeName_inKana>
      <HealthInsurance_Information type="array">
        <HealthInsurance_Information_child type="record">
          <Insurance_Combination_Number type="string">0001</Insurance_Combination_Number>
        </HealthInsurance_Information_child>
      </HealthInsurance_Information>
    </Patient_Information>
  </patientinfores>
</xmlio2>

"""

TEST_ORCA_IS_EXIST_PATIENT_RETURN_DATA = """
<xmlio2>
  <patientlst2res type="record">
    <Information_Date type="string">2014-07-15</Information_Date>
    <Information_Time type="string">17:30:51</Information_Time>
    <Api_Result type="string">00</Api_Result>
    <Api_Result_Message type="string">処理終了</Api_Result_Message>
    <Reskey type="string">Patient Info</Reskey>
    <Target_Patient_Count type="string">002</Target_Patient_Count>
    <No_Target_Patient_Count type="string">000</No_Target_Patient_Count>
    <Patient_Information type="array">
      <Patient_Information_child type="record">
        <Patient_ID type="string">00013</Patient_ID>
        <WholeName type="string">医療　太郎</WholeName>
        <WholeName_inKana type="string">イリョウ　タロウ</WholeName_inKana>
        <BirthDate type="string">1978-02-02</BirthDate>
        <Sex type="string">1</Sex>
        <Home_Address_Information type="record">
          <Address_ZipCode type="string">1130021</Address_ZipCode>
          <WholeAddress1 type="string">東京都文京区本駒込</WholeAddress1>
          <WholeAddress2 type="string">６−１６−３</WholeAddress2>
        </Home_Address_Information>
        <HealthInsurance_Information type="array">
          <HealthInsurance_Information_child type="record">
            <InsuranceProvider_Class type="string">060</InsuranceProvider_Class>
            <InsuranceProvider_WholeName type="string">国保</InsuranceProvider_WholeName>
            <InsuranceProvider_Number type="string">138057</InsuranceProvider_Number>
            <HealthInsuredPerson_Symbol type="string">０１０</HealthInsuredPerson_Symbol>
            <HealthInsuredPerson_Number type="string">８９０１２</HealthInsuredPerson_Number>
            <HealthInsuredPerson_Assistance type="string">3</HealthInsuredPerson_Assistance>
            <RelationToInsuredPerson type="string">1</RelationToInsuredPerson>
            <HealthInsuredPerson_WholeName type="string">日医　次郎</HealthInsuredPerson_WholeName>
            <Certificate_StartDate type="string">2010-08-10</Certificate_StartDate>
            <Certificate_ExpiredDate type="string">9999-12-31</Certificate_ExpiredDate>
          </HealthInsurance_Information_child>
        </HealthInsurance_Information>
        <PublicInsurance_Information type="array">
          <PublicInsurance_Information_child type="record">
            <PublicInsurance_Class type="string">010</PublicInsurance_Class>
            <PublicInsurance_Name type="string">感３７の２</PublicInsurance_Name>
            <PublicInsurer_Number type="string">10131142</PublicInsurer_Number>
            <PublicInsuredPerson_Number type="string">1234566</PublicInsuredPerson_Number>
            <Certificate_IssuedDate type="string">2010-08-10</Certificate_IssuedDate>
            <Certificate_ExpiredDate type="string">9999-12-31</Certificate_ExpiredDate>
          </PublicInsurance_Information_child>
        </PublicInsurance_Information>
      </Patient_Information_child>
    </Patient_Information>
  </patientlst2res>
</xmlio2>
"""

TEST_ORCA_IS_NOT_EXIST_PATIENT_RETURN_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<xmlio2>
<patientlst2res type="record">
<Information_Date type="string">2023-01-12</Information_Date>
<Information_Time type="string">19:27:26</Information_Time>
<Api_Result type="string">20</Api_Result>
<Api_Result_Message type="string">該当患者が存在しません。</Api_Result_Message>
<Reskey type="string">Patient Info</Reskey>
<Target_Patient_Count type="string">000</Target_Patient_Count>
<No_Target_Patient_Count type="string">000</No_Target_Patient_Count>
</patientlst2res>
</xmlio2>
"""

TEST_COMPOSE_IS_PATIENT_XML_DATA = """
            <data>
                <patientlst3req type="record">
                    <WholeName type="string">医療　太郎</WholeName>
                    <Birth_StartDate type="string">2000-08-08</Birth_StartDate>
                    <Birth_EndDate type="string">2000-08-08</Birth_EndDate>
                    <Sex type="string">1</Sex>
                    <InOut type="string"></InOut>
                </patientlst3req>
            </data>
            """

TEST_PATIENT = Patient(**PATIENT_DATA)


def test_sync_patient_to_orca_happy_path():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    orca_session = session, uri

    orca_service = OrcaService(orca_session=orca_session)
    orca_service.create_patient = Mock()
    orca_service.create_patient.return_value = (None, TEST_ORCA_PATIENT_ID)
    err, result = orca_service.sync_patient_to_orca(TEST_PATIENT)

    assert err is None
    assert result == TEST_ORCA_PATIENT_ID


def test_sync_patient_to_orca_failed_with_user_duplicated():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    orca_session = session, uri

    orca_service = OrcaService(orca_session=orca_session)
    orca_service.create_patient = Mock()
    orca_service.create_patient.return_value = (
        Exception("the user already registered on ORCA"),
        TEST_ORCA_PATIENT_ID,
    )
    err, result = orca_service.sync_patient_to_orca(TEST_PATIENT)

    assert err is not None
    assert result == TEST_ORCA_PATIENT_ID


def test_create_patient_happy_path(mocker):
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    expected_api_endpoint = f"{uri}/api/orca12/patientmodv2?class=01"
    orca_session = session, uri

    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_CREATE_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    orca_service = OrcaService(orca_session=orca_session)
    orca_service.is_patient_exist_xml_parser = Mock()
    orca_service.is_patient_exist_xml_parser.return_value = (None, 0, None, None)
    orca_service.is_patient_exist = Mock()
    orca_service.is_patient_exist.return_value = ("User Not Found", None, False)
    orca_service.add_patient_govfund = Mock()

    # When
    err, result = orca_service.create_patient(
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_PHONE_NUMBER,
        TEST_ORCA_PATIENT_EMAIL,
        TEST_ORCA_PATIENT_ZIPCODE,
        TEST_ORCA_PATIENT_ADDRESS,
        TEST_ORCA_PATIENT_STREET_ADDRESS,
    )

    # Then
    session.post.assert_called
    assert f"{expected_api_endpoint}" in session.post.call_args_list.__str__()
    assert err is None
    assert result == TEST_ORCA_PATIENT_ID


def test_create_patient_failed_due_to_patient_duplicated():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    orca_session = session, uri

    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_CREATE_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    orca_service = OrcaService(orca_session=orca_session)
    orca_service.is_patient_exist_xml_parser = Mock()
    orca_service.is_patient_exist_xml_parser.return_value = (
        None,
        0,
        TEST_ORCA_PATIENT_ID,
        None,
        None,
        TEST_ORCA_PATIENT_KANA_NAME,
    )
    orca_service.is_patient_exist = Mock()
    orca_service.is_patient_exist.return_value = ("", TEST_ORCA_PATIENT_ID, True)

    # When
    err, result = orca_service.create_patient(
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_PHONE_NUMBER,
        TEST_ORCA_PATIENT_EMAIL,
        TEST_ORCA_PATIENT_ZIPCODE,
        TEST_ORCA_PATIENT_ADDRESS,
        TEST_ORCA_PATIENT_STREET_ADDRESS,
    )

    # Then

    assert str(err) == str(Exception("the user already registered on ORCA"))
    assert result == TEST_ORCA_PATIENT_ID


def test_compose_create_patient_xml_happy_path():
    orca_service = OrcaService()
    err, result = orca_service.compose_create_patient_xml(
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_EMAIL,
        TEST_ORCA_PATIENT_ZIPCODE,
        TEST_ORCA_PATIENT_ADDRESS,
        TEST_ORCA_PATIENT_STREET_ADDRESS,
        TEST_ORCA_PATIENT_PHONE_NUMBER,
        TEST_ORCA_GOVFUND_DATE,
        TEST_ORCA_GOVFUND_DATE,
    )

    assert err is None
    assert result == TEST_COMPOSE_CREATE_PATIENT_XML_DATA


def test_compose_create_patient_xml_lack_of_item():
    orca_service = OrcaService()
    err, result = orca_service.compose_create_patient_xml(
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        None,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_EMAIL,
        TEST_ORCA_PATIENT_ZIPCODE,
        TEST_ORCA_PATIENT_ADDRESS,
        TEST_ORCA_PATIENT_STREET_ADDRESS,
        None,
        TEST_ORCA_GOVFUND_DATE,
        None,
    )

    assert str(err) == str(Exception("Lack of patient items"))
    assert result is None


def test_add_patient_govfund_happy_path():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    expected_api_endpoint = f"{uri}/api/orca12/patientmodv2?class=04"
    orca_session = session, uri
    orca_service = OrcaService(orca_session=orca_session)
    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_CREATE_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    # When
    err, result = orca_service.add_patient_govfund(
        TEST_ORCA_PATIENT_ID,
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_GOVFUND_CLASS,
        TEST_GOV_FUND_NAME,
        TEST_ORCA_GOVFUND_NUM,
        TEST_ORCA_GOVFUND_PERSON_NUM,
        TEST_ORCA_GOVFUND_DATE,
        TEST_ORCA_GOVFUND_DATE,
    )

    # Then
    session.post.assert_called
    assert f"{expected_api_endpoint}" in session.post.call_args_list.__str__()
    assert err is None
    assert result == TEST_ORCA_PATIENT_ID


def test_add_patient_govfund_lack_of_item():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    expected_api_endpoint = f"{uri}/api/orca12/patientmodv2?class=04"
    orca_session = session, uri
    orca_service = OrcaService(orca_session=orca_session)

    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_CREATE_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    # When
    err, result = orca_service.add_patient_govfund(
        TEST_ORCA_PATIENT_ID,
        TEST_ORCA_PATIENT_NAME,
        None,
        TEST_ORCA_PATIENT_GENDER,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_GOVFUND_CLASS,
        TEST_GOV_FUND_NAME,
        TEST_ORCA_GOVFUND_NUM,
        TEST_ORCA_GOVFUND_PERSON_NUM,
        TEST_ORCA_GOVFUND_DATE,
        TEST_ORCA_GOVFUND_DATE,
    )

    # Then
    session.post.assert_called
    assert f"{expected_api_endpoint}" not in session.post.call_args_list.__str__()
    assert str(err) == str(Exception("Lack of requred data for ORCA"))
    assert result is None


def test_is_patient_exist_exist():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    expected_api_endpoint = f"{uri}/api/api01rv2/patientlst3v2?class=01"
    orca_session = session, uri
    orca_service = OrcaService(orca_session=orca_session)

    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_IS_EXIST_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    # When
    err, orca_patient_id, result = orca_service.is_patient_exist(
        TEST_ORCA_PATIENT_NAME,
        TEST_ORCA_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_PATIENT_GENDER,
    )

    # Then
    session.post.assert_called
    assert f"{expected_api_endpoint}" in session.post.call_args_list.__str__()
    assert err == "Exact match user found"
    assert orca_patient_id == "00013"
    assert result is True


def test_is_patient_exist_not_exist():
    # Given
    session = Mock()
    uri = "https://demo-weborca.cloud.orcamo.jp"
    expected_api_endpoint = f"{uri}/api/api01rv2/patientlst3v2?class=01"
    orca_session = session, uri
    orca_service = OrcaService(orca_session=orca_session)

    reply_value = ORCAReplyData()
    reply_value.__dict__["text"] = TEST_ORCA_IS_NOT_EXIST_PATIENT_RETURN_DATA
    session.post.return_value = reply_value

    # When
    err, orca_patient_id, result = orca_service.is_patient_exist(
        TEST_ORCA_NOT_EXIST_PATIENT_NAME,
        TEST_ORCA_NOT_EXIST_PATIENT_KANA_NAME,
        TEST_ORCA_PATIENT_DOB,
        TEST_ORCA_PATIENT_GENDER,
    )

    # Then
    session.post.assert_called
    assert f"{expected_api_endpoint}" in session.post.call_args_list.__str__()
    assert err == "User Not Found"
    assert orca_patient_id is None
    assert result is False


def test_compose_is_patient_exist_xml_happy_path():
    orca_service = OrcaService()
    err, result = orca_service.compose_is_patient_exist_xml(
        TEST_ORCA_PATIENT_NAME, TEST_ORCA_PATIENT_GENDER, TEST_ORCA_PATIENT_DOB
    )

    assert err is None
    assert result == TEST_COMPOSE_IS_PATIENT_XML_DATA


def test_compose_is_patient_exist_xml_lack_of_items():
    orca_service = OrcaService()
    err, result = orca_service.compose_is_patient_exist_xml(
        TEST_ORCA_PATIENT_NAME, TEST_ORCA_PATIENT_GENDER, None
    )

    assert str(err) == str(Exception("Lack of requred data for ORCA"))
    assert result is None


def test_is_valid_ins_card_xml_parser_pass():
    orca_service = OrcaService()
    err, start_date, expired_date = orca_service.is_valid_ins_card_xml_parser(
        VALID_INSCARD_XML_DATA
    )

    expected_start_date = "2020-01-01"
    expected_expired_date = "9999-01-01"

    assert err is None
    assert expected_start_date == start_date
    assert expected_expired_date == expired_date


def test_is_valid_ins_card_xml_parser_fail():
    orca_service = OrcaService()
    err, start_date, expired_date = orca_service.is_valid_ins_card_xml_parser(
        INVALID_INSCARD_XML_DATA
    )

    expected_start_date = "2020-01-01"
    expected_expired_date = "9999-01-01"

    assert str(err) == str(Exception("provided xml doesn't have valid data"))
    assert expected_start_date != start_date
    assert expected_expired_date != expired_date


def test_compare_name_pass():
    orca_service = OrcaService()
    NAME1 = "斎藤 隆"
    NAME2 = "斎藤 隆"

    assert orca_service.compare_name(NAME1, NAME2) is True


def test_compare_name_fail_invalid_second_name():
    orca_service = OrcaService()
    NAME1 = "斎藤 隆"
    NAME2 = "齋藤 隆"  # type of complex kanji letter of "さいとう"

    assert orca_service.compare_name(NAME1, NAME2) is False


def test_compare_name_fail_invalid_first_name():
    orca_service = OrcaService()
    NAME1 = "斎藤 隆"
    NAME2 = "斉藤 崇"

    assert orca_service.compare_name(NAME1, NAME2) is False


def test_compare_name_fail_invalid_both_name():
    orca_service = OrcaService()
    NAME1 = "斎藤 隆"
    NAME2 = "齋藤 崇"

    assert orca_service.compare_name(NAME1, NAME2) is False
