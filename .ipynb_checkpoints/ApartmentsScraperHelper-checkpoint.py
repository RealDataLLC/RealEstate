def getAddressLink(soup):
    """
    Description: get the address link of the page from a soup object
    """
    return map(lambda a: a["href"], soup.find("section", {"id":"placards"}).find_all("a", {"class": "property-link"}))

def getNumPages(soup):
    """
    Description: find the number of pages that the scraper needs to parse through to get all the addresses
    """
    return int(soup.find("span", {"class": "pageRange"}).text.split()[-1])

def getURLs(bb:str) -> list:
    """
    Description: get the URLs to all the address listing
    
    @param bb: the query param
    @return a list of the URLs to scrape
    """
    addressURLs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip,deflate,br",
        "Accept-Language": "en-US,en;q=.05",
        "Host": "www.apartments.com"
    }
    root = f"https://www.apartments.com/houses/?bb={bb}"
    resp = requests.get(root, headers=headers)
    soup = BeautifulSoup(resp.text)
    addressURLs.extend(getAddressLink(soup))
    for pageNum in range(2, getNumPages(soup)+1):
        resp = requests.get(f"https://www.apartments.com/houses/{pageNum}/?bb={bb}", headers=headers)
        soup = BeautifulSoup(resp.text)
        addressURLs.extend(getAddressLink(soup))
    return addressURLs
def getAll(soup):
    """
    Description: gets data from soup object
    """
    addressData = soup.find("div", {"class": "propertyAddressContainer"}).find_all("span")
    address = addressData[0].text.strip()
    city = addressData[1].text.strip()
    state = addressData[3].text.strip()
    zipcode = addressData[4].text.strip()
    
    neighborhood = soup.find("a", {"class": "neighborhood"}).text.strip()

    propertyBlurbContent = soup.find("p", {"class": "propertyBlurbContent"}).find_all("a")
    county = propertyBlurbContent[0].text.strip()
    attendanceZone = propertyBlurbContent[2].text.strip()

    description = soup.find("section", {"id": "descriptionSection"}).find("p").text

    priceBedBathArea = soup.find("ul", {"class": "priceBedRangeInfo"}).find_all("li")
    rent = priceBedBathArea[0].text.strip()
    bed = priceBedBathArea[1].text.strip()
    bath = priceBedBathArea[2].text.strip()
    sqft = priceBedBathArea[3].text.strip()

    phoneNumber = soup.find("div", {"class": "phoneNumber"}).find("span").text.strip() if soup.find("div", {"class": "phoneNumber"}) else None
    agentName = soup.find("div", {"class": "agentFullName"}).text.strip() if soup.find("div", {"class": "agentFullName"}) else None
    agencyName = soup.find("div", {"class": "agencyName"}).text.strip() if soup.find("div", {"class": "agencyName"}) else None

    return {
        "address": address,
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "neighborhood": neighborhood,
        "county": county,
        "attendanceZone": attendanceZone,
        "description": description,
        "rent": rent.split()[-1].replace("$", "").replace(",", ""),
        "bed": bed.split()[1],
        "bath": bath.split()[1],
        "sqft": sqft.split()[2].replace(",", "") if sqft !="Square Feet" else None,
        "phoneNumber": phoneNumber,
        "agentName": agentName,
        "agencyName": agencyName
    }

def main(bb):
    """
    Description: sends request and writes it to a csv file. Single thread.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip,deflate,br",
        "Accept-Language": "en-US,en;q=.05",
        "Host": "www.apartments.com"
    }
    
    bb = bb
    filename = f"{bb}.csv"
    fieldnames = [
        "address",
        "city",
        "state",
        "zipcode",
        "neighborhood",
        "county",
        "attendanceZone",
        "description",
        "rent",
        "bed",
        "bath",
        "sqft",
        "phoneNumber",
        "agentName",
        "agencyName"
    ]
    with open(filename, "a+") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for addressURL in getURLs(bb):
            print(addressURL)
            resp = requests.get(addressURL, headers=headers)
            if resp.status_code != 200:
                raise Exception("status code not 200")
            soup = BeautifulSoup(resp.text)
            data = getAll(soup)
            time.sleep(1)
            writer.writerow(data)