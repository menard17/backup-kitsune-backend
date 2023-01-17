import datetime
from enum import Enum, auto
from typing import Optional, Tuple
from uuid import UUID
from xml.etree import ElementTree

from fhir.resources.patient import Patient

from adapters.fhir_store import ResourceClient
from services.patient_service import PatientService
from utils.orca_setup import OrcaSingleton


class OrcaService:
    def __init__(self, patient_service=None, orca_session=None, resource_client=None):
        self.resource_client = resource_client or ResourceClient()
        self.orca_session = orca_session or OrcaSingleton().get_session()
        self.patient_service = patient_service or PatientService(self.resource_client)

    def get_orca_data(
        self,
        session,
        orca_uri: str,
        api_endpoint: str,
        request_option: Optional[str],
    ) -> Tuple[Optional[Exception], Optional[str]]:
        try:
            receive_data = session.get(
                orca_uri + f"{api_endpoint}{request_option}",
                headers={"Content-Type": "application/xml"},
            )
        except ConnectionError:
            return Exception("Could't access to ORCA"), None

        return None, receive_data

    def post_orca_data(
        self,
        session,
        orca_uri: str,
        api_endpoint: str,
        request_option: Optional[str],
        xml_data: str,
    ) -> Tuple[Optional[Exception], Optional[str]]:

        try:
            receive_data = session.post(
                orca_uri + f"{api_endpoint}{request_option}",
                headers={"Content-Type": "application/xml"},
                data=xml_data.encode("utf-8"),
            )
        except ConnectionError:
            return Exception("Could't access to ORCA"), None

        return None, receive_data

    def sync_patient_to_orca(
        self,
        patient: Patient,
    ) -> Tuple[Optional[Exception], str]:
        """
        Description:
            functions for syncing patient data to ORCA from FHIR pubsub.
            Do following action here:
                - receive data from FHIR pubsub
                - Patient registration with data of FHIR pubsub
        """
        patient_id = self._render_patient_id(patient)
        email = get_propery_only_value(self._render_email(patient))
        user_name = get_propery_only_value(self._render_full_name(patient))
        user_name_kana = self._render_kana_name(patient)
        phone_number = (
            ""
            if patient is None
            else next(x for x in patient.telecom if x.system == "phone").value
        )
        phone_number = get_propery_only_value(phone_number)

        gender = "" if patient is None or patient.gender is None else patient.gender
        gender = get_propery_only_value(gender)
        orca_gender = self._render_orca_gender(gender)
        dob = (
            ""
            if patient is None or patient.birthDate is None
            else str(patient.birthDate)
        )
        dob = get_propery_only_value(dob)
        zipcode, pref_address, city_address, street_address = self._render_orca_address(
            patient
        )
        address = [
            {
                "line": street_address,
                "city": city_address,
                "state": pref_address,
                "postalCode": zipcode,
            }
        ]
        orca_address = pref_address + city_address
        orca_street_address = street_address[0]
        orca_api_err, orca_patient_id = self.create_patient(
            name=user_name,
            kana_name=user_name_kana,
            dob=dob,
            gender=orca_gender,
            phone_number=phone_number,
            email=email,
            zipcode=zipcode,
            address=orca_address,
            street_address=orca_street_address,
        )
        if orca_api_err:
            return Exception(f"ORCA returns error:{orca_api_err}"), orca_patient_id
        else:
            given_name, family_name = self._render_devided_full_name(patient)
            fhir_err, patient = self.patient_service.update(
                patient_id,
                family_name,
                given_name,
                gender,
                phone_number,
                dob,
                address,
                orca_patient_id,
            )
            if fhir_err:
                return (
                    Exception(f"Send ORCA ID sent failed to FHIR{fhir_err}"),
                    orca_patient_id,
                )

        return None, orca_patient_id

    def _render_patient_id(self, patient: Optional[Patient]) -> UUID:
        if patient is None:
            return ""

        return patient.id

    def _render_email(self, patient: Optional[Patient]) -> Optional[str]:
        if patient is None:
            return ""

        email = next(
            (x for x in patient.telecom if x.system == "email" and x.use == "home"),
            None,
        )
        if email is None:
            return ""

        return email.value

    def _render_devided_full_name(self, patient: Optional[Patient]) -> Tuple[list, str]:
        if patient is None:
            return ("", "")
        name = next((x for x in patient.name if x.use == "official"), None)
        first_name = ["" if len(name.given) == 0 else name.given[0]]
        last_name = name.family
        return first_name, last_name

    def _render_full_name(self, patient: Optional[Patient]) -> Optional[str]:
        if patient is None:
            return ""

        name = next((x for x in patient.name if x.use == "official"), None)
        if name is None:
            return ""

        first_name = "" if len(name.given) == 0 else name.given[0]
        last_name = name.family
        full_name = f"{last_name} {first_name}"
        return full_name

    def _render_kana_name(self, patient: Optional[Patient]) -> Optional[str]:
        if patient is None:
            return ""
        kana_name = next(
            (
                x
                for x in patient.name
                if x.extension and x.extension[0].valueString == "SYL"
            ),
            None,
        )
        if kana_name is None:
            return ""

        kana_first_name = "" if len(kana_name.given) == 0 else kana_name.given[0]
        kana_last_name = kana_name.family
        kana_full_name = f"{kana_last_name} {kana_first_name}"
        return kana_full_name

    def _render_orca_address(
        self, patient: Optional[Patient]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        if patient is None:
            return ""

        address = next((x for x in patient.address if x.use == "home"), None)
        if address is None:
            return ""

        return address.postalCode, address.state, address.city, address.line

    def _render_orca_gender(self, gender: str) -> Optional[int]:
        if gender is None:
            return None
        if gender == "male":
            return 1
        elif gender == "female":
            return 2

    def create_patient(
        self,
        name: str,
        kana_name: str,
        dob: str,
        gender: int,
        phone_number: str,
        email: str,
        zipcode: str,
        address: str,
        street_address: str,
    ) -> Tuple[Exception, str]:
        """
        Description:
        Create patient on ORCA
        - create request xml file
        - confirm existance of patient
        - post xml data to ORCA
        - Add govorment fund
        - return ORCA ID

        Reference:
        https://www.orca.med.or.jp/receipt/tec/api/patientmod.html
        """

        GOV_FUND_CLASS = "094"
        GOV_FUND_NAME = "コロナ軽症"
        GOV_FUND_NUM = 28136802
        GOV_FUND_PERSON_NUM = 9999996
        ORCA_API_ENDPOINT = "/api/orca12/patientmodv2"
        ORCA_API_OPTION = "?class=01"

        _gov_fund_issued_date = _gov_fund_expired_date = (
            datetime.datetime.now().date().isoformat()
        )

        xml_err, xml_data = self.compose_create_patient_xml(
            name,
            kana_name,
            dob,
            gender,
            email,
            zipcode,
            address,
            street_address,
            phone_number,
            _gov_fund_issued_date,
            _gov_fund_expired_date,
        )

        session, orca_uri = self.orca_session
        _, orca_patient_id, is_patient_exist = self.is_patient_exist(
            name, kana_name, dob, gender
        )
        if not is_patient_exist:
            _, receive_data = self.post_orca_data(
                session, orca_uri, ORCA_API_ENDPOINT, ORCA_API_OPTION, xml_data
            )
            xml_err, orca_patient_id = self.create_patient_xml_parser(receive_data.text)
            # This is hardcode for registation of govfund No.094
            self.add_patient_govfund(
                orca_patient_id,
                name,
                kana_name,
                gender,
                dob,
                GOV_FUND_CLASS,
                GOV_FUND_NAME,
                GOV_FUND_NUM,
                GOV_FUND_PERSON_NUM,
                _gov_fund_issued_date,
                _gov_fund_expired_date,
            )
            return None, orca_patient_id
        else:
            return (Exception("the user already registered on ORCA"), orca_patient_id)

    def compose_create_patient_xml(
        self,
        name,
        kana_name,
        dob,
        gender,
        email,
        zipcode,
        address,
        street_address,
        phone_number,
        _gov_fund_issued_date,
        _gov_fund_expired_date,
    ) -> Tuple[Optional[Exception], Optional[str]]:
        """
        Description:
        Compose xml for posting xml to create new user on ORCA
        """

        if (
            name is None
            or kana_name is None
            or dob is None
            or gender is None
            or email is None
            or zipcode is None
            or address is None
            or street_address is None
            or phone_number is None
            or _gov_fund_issued_date is None
            or _gov_fund_expired_date is None
        ):
            return Exception("Lack of patient items"), None
        else:
            xml_data = f"""
            <data>
                <patientmodreq type="record">
                    <Mod_Key type="string">2</Mod_Key>
                    <Patient_ID type="string">*</Patient_ID>
                    <WholeName type="string">{name}</WholeName>
                    <WholeName_inKana type="string">{kana_name}</WholeName_inKana>
                    <BirthDate type="string">{dob}</BirthDate>
                    <Sex type="string">{gender}</Sex>
                    <EmailAddress type="string">{email}</EmailAddress>
                    <Home_Address_Information type="record">
                        <Address_ZipCode type="string">{zipcode}</Address_ZipCode>
                        <WholeAddress1 type="string">{address}</WholeAddress1>
                        <WholeAddress2 type="string">{street_address}</WholeAddress2>
                        <PhoneNumber1 type="string">{phone_number}</PhoneNumber1>
                    </Home_Address_Information>
                    <HealthInsurance_Information type="record">
                        <PublicInsurance_Information type="array">
                            <PublicInsurance_Information_child type="record">
                                <PublicInsurance_Class type="string">093</PublicInsurance_Class>
                                <PublicInsurance_Name type="string">PCR検査</PublicInsurance_Name>
                                <PublicInsurer_Number type="string">28131399</PublicInsurer_Number>
                                <PublicInsuredPerson_Number type="string">9999996</PublicInsuredPerson_Number>
                                <Certificate_IssuedDate type="string">{_gov_fund_issued_date}</Certificate_IssuedDate>
                                <Certificate_ExpiredDate type="string">{_gov_fund_expired_date}</Certificate_IssuedDate>
                            </PublicInsurance_Information_child>
                        </PublicInsurance_Information>
                    </HealthInsurance_Information>
                </patientmodreq>
            </data>
            """

            return None, xml_data

    def create_patient_xml_parser(
        self, xmldata: str
    ) -> Tuple[Optional[Exception], str]:
        """
        Reference:
        ORCA response sample
        https://www.orca.med.or.jp/receipt/tec/api/patientmod.html#ressample
        """
        xmltree = ElementTree.fromstring(xmldata)
        if xmltree.find("patientmodres/Api_Result").text != "00":
            return Exception("ORCA API returns Error"), None
        else:
            orca_patient_id = xmltree.find(
                "patientmodres/Patient_Information/Patient_ID"
            ).text
            return None, orca_patient_id

    def add_patient_govfund(
        self,
        orca_id: str,
        name: str,
        kana_name: str,
        gender: int,
        dob: str,
        gov_fund_class: int,
        gov_fund_name: str,
        gov_fund_num: int,
        gov_fund_person_num: int,
        gov_fund_issued_date: str,
        gov_fund_expired_date: str,
    ) -> Tuple[Optional[Exception], Optional[str]]:
        """
        Description:
        Add govfund to supecified patient on ORCA
          1. compose xml
          2. post xml data to ORCA
          3. return ORCA ID
        """
        ORCA_API_ENDPOINT = "/api/orca12/patientmodv2"
        ORCA_API_OPTION = "?class=04"

        xml_err, xml_data = self.compose_add_patient_govfund_xml(
            orca_id,
            name,
            kana_name,
            gender,
            dob,
            gov_fund_class,
            gov_fund_name,
            gov_fund_num,
            gov_fund_person_num,
            gov_fund_issued_date,
            gov_fund_expired_date,
        )

        session, orca_uri = self.orca_session
        if xml_err:
            return xml_err, None
        else:
            api_err, receive_data = self.post_orca_data(
                session, orca_uri, ORCA_API_ENDPOINT, ORCA_API_OPTION, xml_data
            )
            if api_err:
                return api_err, None
            else:
                xml_err, orca_patient_id = self._add_patient_govfund_xml_parser(
                    receive_data.text
                )
                if xml_err:
                    return xml_err, None
                else:
                    return None, orca_patient_id

    def compose_add_patient_govfund_xml(
        self,
        orca_id: str,
        name: str,
        kana_name: str,
        gender: Optional[int],
        dob: str,
        gov_fund_class: int,
        gov_fund_name: str,
        gov_fund_num: int,
        gov_fund_person_num: int,
        gov_fund_issued_date: str,
        gov_fund_expired_date: str,
    ) -> Tuple[Optional[Exception], Optional[str]]:

        if (
            orca_id is None
            or name is None
            or kana_name is None
            or gender is None
            or dob is None
            or gov_fund_class is None
            or gov_fund_name is None
            or gov_fund_num is None
            or gov_fund_person_num is None
            or gov_fund_issued_date is None
            or gov_fund_expired_date is None
        ):
            return Exception("Lack of requred data for ORCA"), None
        else:
            xml_data = f"""
                <data>
                    <patientmodreq type="record">
                        <Mod_Key type="string">2</Mod_Key>
                        <Patient_ID type="string">{orca_id}</Patient_ID>
                        <WholeName type="string">{name}</WholeName>
                        <WholeName_inKana type="string">{kana_name}</WholeName_inKana>
                        <BirthDate type="string">{dob}</BirthDate>
                        <Sex type="string">{gender}</Sex>
                        <HealthInsurance_Information type="record">
                            <PublicInsurance_Information type="array">
                                <PublicInsurance_Information_child type="record">
                                    <PublicInsurance_Class type="string">{gov_fund_class}</PublicInsurance_Class>
                                    <PublicInsurance_Name type="string">{gov_fund_name}</PublicInsurance_Name>
                                    <PublicInsurer_Number type="string">{gov_fund_num}</PublicInsurer_Number>
                                    <PublicInsuredPerson_Number type="string">{gov_fund_person_num}</PublicInsuredPerson_Number>
                                    <Certificate_IssuedDate type="string">{gov_fund_issued_date}</Certificate_IssuedDate>
                                    <Certificate_ExpiredDate type="string">{gov_fund_expired_date}</Certificate_IssuedDate>
                                </PublicInsurance_Information_child>
                            </PublicInsurance_Information>
                        </HealthInsurance_Information>
                    </patientmodreq>
                </data>
            """

            return None, xml_data

    def _add_patient_govfund_xml_parser(
        self, xmldata: str
    ) -> Tuple[Optional[Exception], Optional[str]]:
        """
        Reference:
        ORCA / modify patient response sample
        https://www.orca.med.or.jp/receipt/tec/api/patientmod.html#ressample
        """

        xmltree = ElementTree.fromstring(xmldata)

        orca_patient_id = xmltree.find(
            "patientmodres/Patient_Information/Patient_ID"
        ).text
        if xmltree.find("patientmodres/Api_Result").text != "00":
            return Exception("something happened on ORCA"), None
        else:
            return None, orca_patient_id

    def is_patient_exist(
        self,
        name: str,
        kana_name: str,
        dob: str,
        gender: int,
    ) -> Tuple[str, Optional[str], Optional[bool]]:
        """
        Description:
        If patient has same name, same dob and gender, return True and orca patient id
        Allow registration if only phone number is different

        1. search patient data by name, dob and gender
        2. validate kana_name for exact match
        3. if validate succeeded return trun else return false

        No need to compare name, dob, gender since query based on those of info to ORCA.
        """
        ORCA_API_ENDPOINT = "/api/api01rv2/patientlst3v2"
        ORCA_API_OPTION = "?class=01"
        xml_err, xml_data = self.compose_is_patient_exist_xml(name, gender, dob)
        if not xml_err:
            session, orca_uri = self.orca_session
            orca_api_err, receive_data = self.post_orca_data(
                session, orca_uri, ORCA_API_ENDPOINT, ORCA_API_OPTION, xml_data
            )
            if not orca_api_err:
                (
                    xml_parse_msg,
                    xml_parse_result_code,
                    orca_patient_id,
                    orca_kana_name,
                ) = self.is_patient_exist_xml_parser(receive_data.text)
                if xml_parse_result_code == 1:
                    return xml_parse_msg, orca_patient_id, True
                elif xml_parse_result_code == 2 and self.compare_name(
                    kana_name, orca_kana_name
                ):
                    return "Exact match user found", orca_patient_id, True
                elif xml_parse_result_code == 2 and not self.compare_name(
                    kana_name, orca_kana_name
                ):
                    return (
                        "Name match user found but kana name is different",
                        None,
                        False,
                    )
                else:
                    return "User Not Found", None, False
            else:
                return orca_api_err, None, None
        else:
            return xml_err, None, None

    def compare_name(self, name: str, name_t: str) -> bool:
        _, last_name, first_name = self._divide_name(name)
        _, t_last_name, t_first_name = self._divide_name(name_t)
        if last_name == t_last_name and first_name != t_first_name:
            return False
        elif last_name != t_last_name and first_name == t_first_name:
            return False
        elif last_name != t_last_name and first_name != t_first_name:
            return False
        else:
            return True

    def compose_is_patient_exist_xml(
        self, name: str, gender: int, dob: str
    ) -> Tuple[Optional[Exception], Optional[str]]:

        if name is None or gender is None or dob is None:
            return Exception("Lack of requred data for ORCA"), None
        else:
            xml_data = f"""
            <data>
                <patientlst3req type="record">
                    <WholeName type="string">{name}</WholeName>
                    <Birth_StartDate type="string">{dob}</Birth_StartDate>
                    <Birth_EndDate type="string">{dob}</Birth_EndDate>
                    <Sex type="string">{gender}</Sex>
                    <InOut type="string"></InOut>
                </patientlst3req>
            </data>
            """
            return None, xml_data

    def is_patient_exist_xml_parser(
        self, xmldata: str
    ) -> Tuple[str, int, Optional[str], Optional[str]]:
        """
        Reference:
        ORCA response sample
        https://www.orca.med.or.jp/receipt/tec/api/patientmod.html#ressample

        validate: kana_name

        """
        xmltree = ElementTree.fromstring(xmldata)
        if xmltree.find("patientlst2res/Api_Result").text != "00":
            return "ORCA API returns Error", 9, None, None
        elif xmltree.find("patientlst2res/Target_Patient_Count").text == "000":
            return "Patient Not Found", 0, None, None
        elif xmltree.find("patientlst2res/Target_Patient_Count").text == "999":
            orca_patient_id = xmltree.find(
                "patientlst2res/Patient_Information/Patient_Information_child/Patient_ID"
            ).text
            return (
                "Same patient name exist over 100",
                1,
                orca_patient_id,
                None,
            )
        else:
            orca_patient_id = xmltree.find(
                "patientlst2res/Patient_Information/Patient_Information_child/Patient_ID"
            ).text
            orca_kana_name = xmltree.find(
                "patientlst2res/Patient_Information/Patient_Information_child/WholeName_inKana"
            ).text
            return (
                "User Found but need validation with kana name",
                2,
                orca_patient_id,
                orca_kana_name,
            )

    def is_ins_card_registered(self, orca_patient_id) -> Tuple[Exception, bool]:
        ORCA_API_ENDPOINT = "/api/api01rv2/patientgetv2"
        ORCA_API_OPTION = f"?id={orca_patient_id}"
        session, orca_uri = self.orca_session
        orca_api_err, receive_data = self.get_orca_data(
            session, orca_uri, ORCA_API_ENDPOINT, ORCA_API_OPTION
        )
        if orca_api_err:
            return orca_api_err, None
        else:
            xmltree = ElementTree.fromstring(receive_data.text)
            try:
                ins_card_data = xmltree.find(
                    "patientinfores/Patient_Information/HealthInsurance_Information/"
                    "HealthInsurance_Information_child/HealthInsuredPerson_Number"
                ).text
                return None, True if ins_card_data else (
                    Exception("Insurance card data isn't found on ORCA"),
                    False,
                )
            except Exception:
                return Exception("Insurance card isn't registed"), False

    def is_valid_ins_card(self, orca_patient_id) -> Tuple[Exception, bool]:
        """
        get ins card data and check existance of valid ins card
        Reference:
        https://www.orca.med.or.jp/receipt/tec/api/patientget.html
        """
        ORCA_API_ENDPOINT = "/api/api01rv2/patientgetv2"
        ORCA_API_OPTION = f"?id={orca_patient_id}"
        session, orca_uri = self.orca_session
        orca_api_err, receive_data = self.get_orca_data(
            session, orca_uri, ORCA_API_ENDPOINT, ORCA_API_OPTION
        )
        if orca_api_err:
            return orca_api_err, None

        err, is_ins_card_regs = self.is_ins_card_registered(orca_patient_id)
        if not is_ins_card_regs:
            return Exception("Insurance card isn't registered"), False
        else:
            err, start_date, expired_date = self.is_valid_ins_card_xml_parser(
                receive_data.text
            )
            if not err:
                return (
                    (None, True)
                    if datetime.date.fromisoformat(expired_date)
                    >= datetime.datetime.now().date()
                    and datetime.date.fromisoformat(start_date)
                    <= datetime.datetime.now().date()
                    else (Exception("Insurance card has not valid by date"), False)
                )

    def is_valid_ins_card_xml_parser(
        self, xml_data: str
    ) -> Tuple[Optional[Exception], Optional[str], Optional[str]]:
        xmltree = ElementTree.fromstring(xml_data)
        try:
            if xmltree.find("patientinfores/Api_Result").text != "00":
                return Exception("ORCA API returns Error"), None, None
            else:
                start_date = xmltree.find(
                    "patientinfores/Patient_Information/HealthInsurance_Information/"
                    "HealthInsurance_Information_child/Certificate_StartDate"
                ).text
                expired_date = xmltree.find(
                    "patientinfores/Patient_Information/HealthInsurance_Information/"
                    "HealthInsurance_Information_child/Certificate_ExpiredDate"
                ).text
                return None, start_date, expired_date
        except Exception:
            return Exception("provided xml doesn't have valid data"), None, None

    def _divide_name(self, name: str) -> Tuple[Optional[Exception], str, Optional[str]]:
        if "\u3000" in name:
            last_name, first_name = name.split("\u3000", 1)
            return None, last_name, first_name
        elif " " in name:
            last_name, first_name = name.split(" ", 1)
            return None, last_name, first_name
        else:
            return Exception("Name has not space at least one"), name, None


class PropertyType(Enum):
    Text = auto()
    Date = auto()


def get_propery_value(value: str, type: PropertyType = PropertyType.Text):
    if type == PropertyType.Date:
        return {"date": {"start": value}}
    return {"rich_text": [{"text": {"content": value}}]}


def get_propery_only_value(value: str, type: PropertyType = PropertyType.Text):
    if type == PropertyType.Date:
        return value
    return value
