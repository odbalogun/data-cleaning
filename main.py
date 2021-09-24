
OPENREFINE_HOST = "http://127.0.0.1:3333"

COLUMNS_TO_DELETE = ['Unnamed: 0', 'form.health_centre_information.facility_type_other',
                   'form.health_centre_information.managing_authority_other', 'form.ql_human_resources.choice_labels',
                   'form.ql_information_education_communication.choice_labels', 'form.ql_surveillance.choice_labels',
                   'form.ql_triage_and_early_recognition.choice_labels', 'form.ql_chw.choice_labels',
                   'form.ql_isolation_physical_distancing.choice_labels',
                   'form.grp_infection_prevention_and_control.ql_ppe.choice_labels',
                   'form.grp_infection_prevention_and_control.ql_ppe_plan.choice_labels',
                   'form.grp_infection_prevention_and_control.ql_waste_collection_and_disposal.choice_labels',
                   'form.grp_infection_prevention_and_control.ql_water_sanitation_and_hygiene.choice_labels',
                   'form.grp_infection_prevention_and_control.ql_disinfection_and_sterilization.choice_labels',
                   'form.ql_logistics_patient_and_sample_transfer.choice_labels', 'form.question10.choice_labels',
                   'form.question6.choice_labels', 'form.question2.choice_labels', 'form.question7.choice_labels',
                   'form.question4.choice_labels', 'form.question1.choice_labels']


def using_open_refine(filename):
    import requests
    import uuid
    import io
    import pandas as pd
    from urllib.parse import parse_qs, urlparse

    # get csrf token
    csrf_token_response = requests.get(OPENREFINE_HOST+"/command/core/get-csrf-token")
    token = csrf_token_response.json()['token']

    # converting to csv because of NullPointerException when processing excel sheets
    if filename.split('.')[1] in ['xls', 'xlsx']:
        read_file = pd.read_excel(filename)
        read_file.to_csv("converted.csv", index=None, header=True)
        filename = "converted.csv"

    # create project
    file_upload = {'project-file': open(filename, 'rb')}

    # add unique string to project name
    payload = {'project-name': f"Health Facility Assessment-{str(uuid.uuid4())[:5]}"}
    response = requests.post(OPENREFINE_HOST+"/command/core/create-project-from-upload?csrf_token="+token,
                             files=file_upload, data=payload)

    # get project id
    project_id = parse_qs(urlparse(response.url).query)['project']

    # delete first column (as it is a duplicate of the second column) and other empty columns
    for column in COLUMNS_TO_DELETE:
        response = requests.post(f"{OPENREFINE_HOST}/command/core/remove-column?csrf_token={token}",
                                 data={'columnName': column, 'project': project_id})

    # create pandas dataframe
    # Though the OpenRefine dashboard is extremely powerful and intuitive, its API is very poorly documented.
    # As such the rest of cleaning will be done in pandas
    exported_rows = requests.post(f"{OPENREFINE_HOST}/command/core/export-rows?csrf_token={token}",
                                  data={'project': project_id, 'format': 'csv'}).content
    df = pd.read_csv(io.StringIO(exported_rows.decode('utf-8')))

    # replace "---" with null
    df.replace('---', pd.NA, inplace=True)

    # remove rows without facility name and region info as they can skew ML results unfairly
    df.dropna(subset=["form.health_centre_information.facility_name",
                      "form.health_centre_information.location_information.region_province"], inplace=True)

    # remove duplicates
    df.drop_duplicates(inplace=True)

    # reset dataframe index
    df.reset_index()

    # save data as a csv file
    df.to_csv("output.csv", index=None, header=True)

    # delete OpenRefine project
    payload = {'project': project_id, 'csrf_token': token}
    requests.post(OPENREFINE_HOST+"/command/core/delete-project", data=payload)

    print("The cleaned data has been saved as: output.csv")


def using_pandas(filename):
    import pandas as pd

    # read file
    if filename.split('.')[1] in ['xls', 'xlsx']:
        df = pd.read_excel(filename)
    else:
        df = pd.read_csv(filename)

    # delete first column as it is a duplicate of the second column
    # also delete empty columns
    df.drop(COLUMNS_TO_DELETE, inplace=True, axis=1)

    # replace "---" with null
    df.replace('---', pd.NA, inplace=True)

    # remove rows without facility name and region info as they can skew ML results unfairly
    df.dropna(subset=["form.health_centre_information.facility_name",
                      "form.health_centre_information.location_information.region_province"], inplace=True)

    # remove duplicates
    df.drop_duplicates(inplace=True)

    # reset dataframe index
    df.reset_index()

    # save data as a csv file
    df.to_csv("output.csv", index=None, header=True)
    print("The cleaned data has been saved as: output.csv")


def main():
    print("""Choose a data cleaning tool:
    1) Use Open Refine
    2) Use Pandas
    """)
    try:
        operation = int(input("Choice: "))
    except ValueError:
        print("Invalid operation selected")
        exit()
    filename = input("Enter file name: ")
    if not filename:
        print("Provide a file name")
        exit()
    if operation == 1:
        using_open_refine(filename)
    elif operation == 2:
        using_pandas(filename)
    else:
        print("Invalid operation selected")
        exit()


if __name__ == '__main__':
    main()