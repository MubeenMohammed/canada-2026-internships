from datetime import datetime
import util


def main():

    listings = util.getListingsFromJSON()

    # validate all listings
    util.checkSchema(listings)

    # sort all listings together
    all_listings = util.sortListings(listings)

    # create table and embed all listings in the main README
    util.embedTable(all_listings, "README.md")

    util.setOutput("commit_message", "Updating READMEs at " + datetime.now().strftime("%B %d, %Y %H:%M:%S"))


if __name__ == "__main__":
    main()